"""
测试剪枝和量化后的模型
"""
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

from nets.facenet import Facenet
from utils.dataloader import FacenetDataset, dataset_collate
from utils.utils import get_num_classes


def load_model(model_path, num_classes, backbone='mobilenet', device='cuda'):
    """加载模型"""
    print(f"加载模型: {model_path}")

    model = Facenet(backbone=backbone, num_classes=num_classes, pretrained=False)
    model_dict = model.state_dict()

    pretrained_dict = torch.load(model_path, map_location=device)
    temp_dict = {}

    for k, v in pretrained_dict.items():
        if k in model_dict.keys() and np.shape(model_dict[k]) == np.shape(v):
            temp_dict[k] = v

    model_dict.update(temp_dict)
    model.load_state_dict(model_dict)

    model = model.cuda() if torch.cuda.is_available() else model
    model.eval()

    print(f"成功加载 {len(temp_dict)} 个权重")
    return model


def evaluate(model, data_loader, device):
    """评估模型准确率"""
    model.eval()
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(data_loader):
            images = images.to(device)
            labels = labels.to(device)

            # 前向传播
            _, outputs = model(images, mode="train")

            # 计算准确率
            _, predicted = torch.max(outputs, 1)
            total_correct += (predicted == labels).sum().item()
            total_samples += labels.size(0)

    accuracy = total_correct / total_samples if total_samples > 0 else 0
    model.train()
    return accuracy


def test_pruned_quantized():
    """测试剪枝和量化模型"""
    # 配置
    test_annotation_path = "cls_test.txt"
    num_classes = get_num_classes("cls_train.txt")
    batch_size = 16
    backbone = "mobilenet"
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    print("="*50)
    print("模型评估")
    print("="*50)
    print(f"类别数: {num_classes}")
    print(f"设备: {device}")

    # 检查测试集
    if not os.path.exists(test_annotation_path):
        print(f"警告: 测试集文件不存在 ({test_annotation_path})")
        print("将使用验证集进行测试")
        test_annotation_path = "cls_test.txt"

    with open(test_annotation_path, "r", encoding='utf-8') as f:
        lines_test = f.readlines()

    print(f"测试样本数: {len(lines_test)}")

    # 创建数据加载器
    test_dataset = FacenetDataset(
        input_shape=[160, 160, 3],
        lines=lines_test,
        num_classes=num_classes,
        random=False
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        collate_fn=dataset_collate
    )

    # 测试模型
    model_paths = [
        ('logs_robust/best_model.pth', '最佳训练模型'),
        ('logs_robust/model_pruned.pth', '剪枝后模型'),
        ('logs_robust/model_quantized.pth', '剪枝+量化模型'),
    ]

    results = []
    for model_path, desc in model_paths:
        if os.path.exists(model_path):
            try:
                model = load_model(model_path, num_classes, backbone, device)

                # 检查是否是量化模型
                is_quantized = 'quantized' in model_path

                # 如果是量化模型，需要特殊处理
                if is_quantized:
                    print(f"\n测试 {desc} ({model_path})...")
                    # 动态量化模型
                    try:
                        accuracy = evaluate(model, test_loader, device)
                    except:
                        print("量化模型评估失败，尝试重新量化...")
                        model = torch.quantization.quantize_dynamic(
                            model,
                            {nn.Conv2d, nn.Linear},
                            dtype=torch.qint8
                        )
                        accuracy = evaluate(model, test_loader, device)
                else:
                    print(f"\n测试 {desc} ({model_path})...")
                    accuracy = evaluate(model, test_loader, device)

                results.append((desc, accuracy))
                print(f"  {desc} 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
            except Exception as e:
                print(f"  加载失败: {e}")
        else:
            print(f"\n模型不存在: {model_path}")

    # 打印总结
    print("\n" + "="*50)
    print("测试结果总结")
    print("="*50)
    for desc, acc in results:
        status = "✓" if acc >= 0.92 else "✗"
        print(f"  {status} {desc}: {acc:.4f} ({acc*100:.2f}%)")

    if results:
        best_desc, best_acc = max(results, key=lambda x: x[1])
        print(f"\n最佳模型: {best_desc} ({best_acc:.4f})")

        if best_acc >= 0.92:
            print("✓ 已达到0.92测试准确率目标!")
        else:
            print(f"✗ 未达到0.92目标 (差距: {0.92 - best_acc:.4f})")
            print("\n建议:")
            print("  1. 增加训练epoch数")
            print("  2. 调整剪枝稀疏度")
            print("  3. 增加数据增强")
            print("  4. 使用更大的学习率预热")


if __name__ == "__main__":
    test_pruned_quantized()
