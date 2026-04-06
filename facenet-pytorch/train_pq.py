"""
Facenet训练脚本 - 包含剪枝和量化
用于解决小数据集(600+图片, 115类)过拟合问题
"""

import os
from functools import partial

import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

from nets.facenet import Facenet
from nets.facenet_training import (get_lr_scheduler, set_optimizer_lr,
                                   triplet_loss, weights_init)
from nets.mobilenet import conv_bn, conv_dw, MobileNetV1
from utils.callback import LossHistory
from utils.dataloader import FacenetDataset, LFWDataset, dataset_collate
from utils.utils import (get_num_classes, seed_everything, show_config,
                         worker_init_fn)
from utils.utils_fit import fit_one_epoch


#----------------------------#
#   剪枝配置
#----------------------------#
class PruningConfig:
    """剪枝配置"""
    def __init__(self):
        # 初始剪枝率
        self.initial_sparsity = 0.0
        # 最终剪枝率 (移除50%的权重)
        self.final_sparsity = 0.5
        # 哪些层进行剪枝
        self.prune_backbone = True
        self.prune_classifier = False
        # 使用L1范数进行剪枝
        self.pruning_method = 'l1'


#----------------------------#
#   量化配置
#----------------------------#
class QuantizationConfig:
    """量化配置"""
    def __init__(self):
        # 量化方式: 'dynamic' (训练后动态量化) 或 'static' (静态量化)
        self.quant_type = 'dynamic'
        # INT8量化
        self.dtype = torch.qint8
        # 融合操作 (可用于静态量化)
        self.fuse_modules = [['Bottleneck', 'last_bn']]


def check_backbone_layers(model):
    """检查backbone中的可剪枝层"""
    prunable_layers = []
    for name, module in model.backbone.model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            prunable_layers.append((name, module))
    return prunable_layers


def create_pruning_mask(module, method='l1'):
    """
    创建剪枝掩码
    method: 'l1' 使用L1范数, 'random' 随机剪枝
    """
    if method == 'l1':
        # 计算L1范数
        if isinstance(module, nn.Conv2d):
            # 对卷积核计算L1范数
            weight = module.weight.data.abs()
            # 每个filter的L1范数
            criteria = weight.view(weight.size(0), -1).norm(dim=1)
        elif isinstance(module, nn.Linear):
            weight = module.weight.data.abs()
            criteria = weight.norm(dim=1)
        else:
            return None
        return criteria
    return None


def unstructured_prune(model, sparsity=0.5, exclude_idx=None):
    """
    对模型进行非结构化剪枝 (L1范数)
    sparsity: 0.5 表示剪枝50%的权重
    """
    print(f"开始剪枝, 目标稀疏度: {sparsity}")
    prunable_params = []

    # 收集所有可剪枝的卷积层
    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            prunable_params.append((name, module, 'weight'))

    # 按L1范数排序并剪枝
    for name, module, param_name in prunable_params:
        weight = module.weight.data.abs()
        # 计算每个filter的L1范数
        filter_norms = weight.view(weight.size(0), -1).norm(dim=1)

        # 确定剪枝阈值
        k = int(filter_norms.size(0) * sparsity)
        if k == 0:
            continue

        # 找到L1范数最小的k个filter
        threshold = filter_norms.kthvalue(k)[0]

        # 创建掩码 (保留大于阈值的filter)
        mask = filter_norms.gt(threshold).float()
        mask = mask.view(-1, 1, 1, 1) if len(weight.shape) == 4 else mask.view(-1, 1)

        # 应用掩码
        module.weight.data.mul_(mask)

        # 统计剪枝比例
        pruned = (mask == 0).sum().item()
        total = mask.numel()
        print(f"  剪枝层 {name}: 剪枝 {pruned}/{total} ({100*pruned/total:.1f}%)")

    return model


def prune_model_by_threshold(model, sparsity=0.5):
    """
    通过阈值对模型进行剪枝
    保留最重要的权重，剪掉不重要的
    """
    print(f"\n使用阈值方法剪枝, 稀疏度: {sparsity}")

    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            # 获取权重
            weight = module.weight.data
            # 计算每个output channel的L1范数
            channel_norms = weight.abs().sum(dim=(1, 2, 3))

            # 计算阈值
            k = int(len(channel_norms) * sparsity)
            threshold = channel_norms.kthvalue(k)[0]

            # 创建掩码
            mask = channel_norms.gt(threshold).float().view(-1, 1, 1, 1)
            module.weight.data.mul_(mask)

        elif isinstance(module, nn.Linear) and 'classifier' in name:
            weight = module.weight.data
            channel_norms = weight.abs().sum(dim=1)
            k = int(len(channel_norms) * sparsity)
            if k > 0:
                threshold = channel_norms.kthvalue(k)[0]
                mask = channel_norms.gt(threshold).float().view(-1, 1)
                module.weight.data.mul_(mask)


def count_zero_weights(model):
    """统计模型中零值的比例"""
    total = 0
    zeros = 0
    for module in model.modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            weight = module.weight.data
            total += weight.numel()
            zeros += (weight == 0).sum().item()
    return zeros / total if total > 0 else 0


def apply_quantization(model, quant_type='dynamic'):
    """
    对模型进行量化
    quant_type: 'dynamic' 动态量化, 'static' 静态量化
    """
    print(f"\n开始量化, 类型: {quant_type}")

    model.eval()

    if quant_type == 'dynamic':
        # 动态量化 - 最简单，对权重进行INT8量化
        # 适用于推理时延迟不关键但需要减小模型大小的场景
        model_int8 = torch.quantization.quantize_dynamic(
            model,
            {nn.Conv2d, nn.Linear},
            dtype=torch.qint8
        )
        print("动态量化完成 (INT8)")
        return model_int8

    elif quant_type == 'static':
        # 静态量化 - 需要校准数据集
        model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(model, inplace=True)
        print("静态量化模型已准备, 需要校准")
        return model

    elif quant_type == 'pruned_quantized':
        # 剪枝后量化 - 先剪枝再量化
        print("执行剪枝+量化")
        model = prune_model_by_threshold(model, sparsity=0.5)

        # 动态量化
        model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(model, inplace=True)
        print("剪枝+量化模型已准备")

        return model

    return model


def evaluate_model(model, gen_val, epoch_step_val, device):
    """评估模型准确率"""
    model.eval()
    total_accuracy = 0

    with torch.no_grad():
        for iteration, batch in enumerate(gen_val):
            if iteration >= epoch_step_val:
                break
            images, labels = batch
            images = images.to(device)
            labels = labels.to(device)

            _, outputs2 = model(images, mode="train")
            accuracy = torch.mean(
                (torch.argmax(F.softmax(outputs2, dim=-1), dim=-1) == labels).float()
            )
            total_accuracy += accuracy.item()

    avg_accuracy = total_accuracy / epoch_step_val if epoch_step_val > 0 else 0
    model.train()
    return avg_accuracy


def train_with_pruning():
    """
    完整的剪枝+量化训练流程
    """
    # ========== 基础配置 ==========
    Cuda = True
    seed = 11
    distributed = False
    sync_bn = False
    fp16 = False

    # 数据集配置
    annotation_path = "cls_train.txt"
    input_shape = [160, 160, 3]
    backbone = "mobilenet"
    model_path = "model_data/facenet_mobilenet.pth"
    pretrained = False

    # 训练配置
    batch_size = 48
    Init_Epoch = 0
    Epoch = 50  # 适度训练，避免过拟合

    Init_lr = 1e-3
    Min_lr = Init_lr * 0.01
    optimizer_type = "adam"
    momentum = 0.9
    weight_decay = 1e-4  # 增加正则化
    lr_decay_type = "cos"

    save_period = 5
    save_dir = 'logs_pruned'
    num_workers = 4

    lfw_eval_flag = False
    lfw_dir_path = "lfw"
    lfw_pairs_path = "model_data/lfw_pair.txt"

    # 剪枝配置
    prune_enabled = True
    prune_start_epoch = 5  # 预热后开始剪枝
    prune_final_sparsity = 0.5  # 50%稀疏度

    # 量化配置
    quantize_enabled = True
    quantize_after_epoch = 45  # 训练后期量化

    seed_everything(seed)

    # ========== 设置设备 ==========
    ngpus_per_node = torch.cuda.device_count()
    if distributed:
        dist.init_process_group(backend="nccl")
        local_rank = int(os.environ["LOCAL_RANK"])
        device = torch.device("cuda", local_rank)
    else:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        local_rank = 0

    num_classes = get_num_classes(annotation_path)
    print(f"类别数: {num_classes}")

    # ========== 载入模型 ==========
    model = Facenet(backbone=backbone, num_classes=num_classes, pretrained=pretrained)

    if model_path != '':
        print(f'Load weights {model_path}.')
        model_dict = model.state_dict()
        pretrained_dict = torch.load(model_path, map_location=device)
        temp_dict = {}
        for k, v in pretrained_dict.items():
            if k in model_dict.keys() and np.shape(model_dict[k]) == np.shape(v):
                temp_dict[k] = v
        model_dict.update(temp_dict)
        model.load_state_dict(model_dict)
        print(f"成功加载 {len(temp_dict)} 个权重")

    # ========== 损失函数和优化器 ==========
    loss = triplet_loss()

    if local_rank == 0:
        loss_history = LossHistory(save_dir, model, input_shape=input_shape)
    else:
        loss_history = None

    # AMP混合精度
    if fp16:
        from torch.cuda.amp import GradScaler
        scaler = GradScaler()
    else:
        scaler = None

    model.train()

    # ========== 数据加载 ==========
    val_annotation_path = "cls_val.txt"
    with open(annotation_path, "r", encoding='utf-8') as f:
        lines_train = f.readlines()
    with open(val_annotation_path, "r", encoding='utf-8') as f:
        lines_val = f.readlines()

    np.random.seed(10101)
    np.random.shuffle(lines_train)
    np.random.seed(None)

    num_train = len(lines_train)
    num_val = len(lines_val)

    print(f"训练集: {num_train}, 验证集: {num_val}")

    # 学习率
    nbs = 64
    lr_limit_max = 1e-3 if optimizer_type == 'adam' else 1e-1
    lr_limit_min = 3e-4 if optimizer_type == 'adam' else 5e-4
    Init_lr_fit = min(max(batch_size / nbs * Init_lr, lr_limit_min), lr_limit_max)
    Min_lr_fit = min(max(batch_size / nbs * Min_lr, lr_limit_min * 1e-2), lr_limit_max * 1e-2)

    optimizer = {
        'adam': optim.Adam(model.parameters(), Init_lr_fit, betas=(momentum, 0.999), weight_decay=weight_decay),
        'sgd': optim.SGD(model.parameters(), Init_lr_fit, momentum=momentum, nesterov=True, weight_decay=weight_decay)
    }[optimizer_type]

    lr_scheduler_func = get_lr_scheduler(lr_decay_type, Init_lr_fit, Min_lr_fit, Epoch)

    epoch_step = num_train // batch_size
    epoch_step_val = num_val // batch_size

    if epoch_step == 0 or epoch_step_val == 0:
        raise ValueError("数据集过小")

    # 数据集
    train_dataset = FacenetDataset(input_shape, lines_train, num_classes, random=True)
    val_dataset = FacenetDataset(input_shape, lines_val, num_classes, random=False)

    gen = DataLoader(
        train_dataset, shuffle=True, batch_size=batch_size // 3, num_workers=num_workers,
        pin_memory=True, drop_last=True, collate_fn=dataset_collate
    )
    gen_val = DataLoader(
        val_dataset, shuffle=False, batch_size=batch_size // 3, num_workers=num_workers,
        pin_memory=True, drop_last=True, collate_fn=dataset_collate
    )

    # ========== 主训练循环 ==========
    print("\n" + "="*50)
    print("开始剪枝+量化训练")
    print("="*50)

    best_accuracy = 0.0

    for epoch in range(Init_Epoch, Epoch):
        set_optimizer_lr(optimizer, lr_scheduler_func, epoch)

        # ---- 剪枝 ----
        if prune_enabled and epoch >= prune_start_epoch:
            # 线性增加稀疏度
            current_sparsity = prune_final_sparsity * min(1.0, (epoch - prune_start_epoch) / (Epoch - prune_start_epoch - 10))
            if current_sparsity > 0.1:
                print(f"\n>>> Epoch {epoch+1}: 执行剪枝 (稀疏度: {current_sparsity:.2%})")
                model = prune_model_by_threshold(model, sparsity=current_sparsity)
                zero_ratio = count_zero_weights(model)
                print(f">>> 当前零权重比例: {zero_ratio:.2%}")

        # ---- 训练 ----
        fit_one_epoch(
            model_train=model, model=model, loss_history=loss_history, loss=loss,
            optimizer=optimizer, epoch=epoch, epoch_step=epoch_step, epoch_step_val=epoch_step_val,
            gen=gen, gen_val=gen_val, Epoch=Epoch, Cuda=Cuda, test_loader=None,
            Batch_size=batch_size // 3, lfw_eval_flag=False, fp16=fp16, scaler=scaler,
            save_period=save_period, save_dir=save_dir, local_rank=local_rank
        )

        # ---- 验证准确率 ----
        val_accuracy = evaluate_model(model, gen_val, epoch_step_val, device)
        print(f"Epoch {epoch+1}/{Epoch} 验证准确率: {val_accuracy:.4f}")

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            torch.save(model.state_dict(), os.path.join(save_dir, 'best_model.pth'))
            print(f">>> 保存最佳模型, 准确率: {best_accuracy:.4f}")

        # ---- 量化 ----
        if quantize_enabled and epoch >= quantize_after_epoch and epoch == quantize_after_epoch:
            print("\n" + "="*50)
            print("开始量化")
            print("="*50)
            model_quantized = apply_quantization(model, quant_type='dynamic')

            # 保存量化模型
            torch.save(model_quantized.state_dict(), os.path.join(save_dir, 'model_quantized.pth'))
            print("量化模型已保存")

            # 验证量化模型精度
            val_accuracy_q = evaluate_model(model_quantized, gen_val, epoch_step_val, device)
            print(f"量化后验证准确率: {val_accuracy_q:.4f}")

    print("\n" + "="*50)
    print(f"训练完成! 最佳准确率: {best_accuracy:.4f}")
    print("="*50)

    # ========== 最终处理 ==========
    # 1. 最终剪枝到目标稀疏度
    print("\n执行最终剪枝...")
    model_final = prune_model_by_threshold(model, sparsity=prune_final_sparsity)
    torch.save(model_final.state_dict(), os.path.join(save_dir, 'model_pruned_final.pth'))

    # 2. 量化
    print("执行最终量化...")
    model_final_quantized = apply_quantization(model_final, quant_type='dynamic')
    torch.save(model_final_quantized.state_dict(), os.path.join(save_dir, 'model_pruned_quantized.pth'))

    print("\n所有模型已保存到:", save_dir)

    return model_final_quantized, best_accuracy


def main():
    """主函数"""
    os.makedirs('logs_pruned', exist_ok=True)
    model, accuracy = train_with_pruning()

    print("\n" + "="*50)
    print("最终结果:")
    print(f"  最佳验证准确率: {accuracy:.4f}")
    print(f"  目标准确率: 0.92")
    if accuracy >= 0.92:
        print("  状态: ✓ 达到目标!")
    else:
        print(f"  状态: 需要调整 (差距: {0.92 - accuracy:.4f})")
    print("="*50)


if __name__ == "__main__":
    main()
