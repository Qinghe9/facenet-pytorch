"""
针对小数据集的鲁棒训练脚本
包含: 强正则化 + 剪枝 + 量化
目标: 防止过拟合，达到0.92测试准确率
"""
import os
from functools import partial

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torch.utils.data.dataset import Dataset
from PIL import Image, ImageEnhance
import random


class StrongAugmentationDataset(Dataset):
    """
    强数据增强的数据集
    适用于小数据集(600+图片, 115类)
    """

    def __init__(self, input_shape, lines, num_classes, random=True):
        self.input_shape = input_shape
        self.lines = lines
        self.num_classes = num_classes
        self.random = random
        self.length = len(lines)

        self.paths = []
        self.labels = []
        self.load_dataset()

    def __len__(self):
        return self.length

    def load_dataset(self):
        for path in self.lines:
            path_split = path.split(";")
            self.paths.append(path_split[1].split()[0])
            self.labels.append(int(path_split[0]))
        self.paths = np.array(self.paths, dtype=object)
        self.labels = np.array(self.labels)

    def rand(self, a=0, b=1):
        return np.random.rand() * (b - a) + a

    def cvtColor(self, image):
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image

    def preprocess_input(self, image):
        image = np.array(image, dtype=np.float32) / 255.0
        return image

    def resize_image(self, image, size, letterbox_image):
        iw, ih = image.size
        w, h = size
        if letterbox_image:
            scale = min(w / iw, h / ih)
            nw = int(iw * scale)
            nh = int(ih * scale)
            image = image.resize((nw, nh), Image.BICUBIC)
            new_image = Image.new('RGB', size, (128, 128, 128))
            new_image.paste(image, ((w - nw) // 2, (h - nh) // 2))
        else:
            new_image = image.resize((w, h), Image.BICUBIC)
        return new_image

    def geometric_transform(self, image):
        """几何变换增强"""
        if random.random() < 0.5 and self.random:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # 随机旋转 (-15 ~ +15度)
        if random.random() < 0.3 and self.random:
            angle = random.uniform(-15, 15)
            image = image.rotate(angle, resample=Image.BICUBIC)

        # 随机裁剪和缩放
        if random.random() < 0.3 and self.random:
            scale = random.uniform(0.9, 1.0)
            w, h = image.size
            new_w, new_h = int(w * scale), int(h * scale)
            left = random.randint(0, w - new_w)
            top = random.randint(0, h - new_h)
            image = image.crop((left, top, left + new_w, top + new_h))
            image = image.resize((w, h), Image.BICUBIC)

        return image

    def color_jitter(self, img):
        """颜色抖动"""
        if random.random() < 0.5 and self.random:
            # 亮度
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Brightness(img).enhance(factor)

        if random.random() < 0.5 and self.random:
            # 对比度
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Contrast(img).enhance(factor)

        if random.random() < 0.5 and self.random:
            # 颜色
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Color(img).enhance(factor)

        if random.random() < 0.5 and self.random:
            # 锐度
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Sharpness(img).enhance(factor)

        return img

    def __getitem__(self, index):
        images = np.zeros((3, 3, self.input_shape[0], self.input_shape[1]))
        labels = np.zeros((3,))

        # 选择同类样本
        c = random.randint(0, self.num_classes - 1)
        selected_path = self.paths[self.labels[:] == c]
        while len(selected_path) < 2:
            c = random.randint(0, self.num_classes - 1)
            selected_path = self.paths[self.labels[:] == c]

        # 选择anchor和positive
        image_indexes = np.random.choice(range(0, len(selected_path)), 2)

        for i, idx in enumerate(image_indexes):
            image = self.cvtColor(Image.open(selected_path[idx]))
            image = self.geometric_transform(image)
            image = self.color_jitter(image)
            image = self.resize_image(image, [self.input_shape[1], self.input_shape[0]], True)
            image = self.preprocess_input(np.array(image, dtype='float32'))
            image = np.transpose(image, [2, 0, 1])
            images[i, :, :, :] = image
            labels[i] = c

        # 选择negative
        different_c = list(range(self.num_classes))
        different_c.pop(c)
        different_c_index = np.random.choice(range(0, self.num_classes - 1))
        current_c = different_c[different_c_index]
        selected_path = self.paths[self.labels == current_c]
        while len(selected_path) < 1:
            different_c_index = np.random.choice(range(0, self.num_classes - 1))
            current_c = different_c[different_c_index]
            selected_path = self.paths[self.labels == current_c]

        image_indexes = np.random.choice(range(0, len(selected_path)), 1)
        image = self.cvtColor(Image.open(selected_path[image_indexes[0]]))
        image = self.geometric_transform(image)
        image = self.color_jitter(image)
        image = self.resize_image(image, [self.input_shape[1], self.input_shape[0]], True)
        image = self.preprocess_input(np.array(image, dtype='float32'))
        image = np.transpose(image, [2, 0, 1])
        images[2, :, :, :] = image
        labels[2] = current_c

        return images, labels


def dataset_collate(batch):
    """与原始collate相同"""
    images = []
    labels = []
    for img, label in batch:
        images.append(img)
        labels.append(label)

    images1 = np.array(images)[:, 0, :, :, :]
    images2 = np.array(images)[:, 1, :, :, :]
    images3 = np.array(images)[:, 2, :, :, :]
    images = np.concatenate([images1, images2, images3], 0)

    labels1 = np.array(labels)[:, 0]
    labels2 = np.array(labels)[:, 1]
    labels3 = np.array(labels)[:, 2]
    labels = np.concatenate([labels1, labels2, labels3], 0)

    images = torch.from_numpy(np.array(images)).type(torch.FloatTensor)
    labels = torch.from_numpy(np.array(labels)).long()
    return images, labels


class LabelSmoothingCrossEntropy(nn.Module):
    """标签平滑交叉熵损失 - 防止过拟合"""

    def __init__(self, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing

    def forward(self, pred, target):
        n_classes = pred.size(-1)
        log_preds = F.log_softmax(pred, dim=-1)

        # 标签平滑
        with torch.no_grad():
            true_dist = torch.zeros_like(log_preds)
            true_dist.fill_(self.smoothing / (n_classes - 1))
            true_dist.scatter_(1, target.unsqueeze(1), 1.0 - self.smoothing)

        return torch.mean(torch.sum(-true_dist * log_preds, dim=-1))


def train_robust():
    """鲁棒训练主函数"""
    # ========== 配置 ==========
    Cuda = True
    seed = 11
    distributed = False

    # 数据
    annotation_path = "cls_train.txt"
    val_annotation_path = "cls_val.txt"
    input_shape = [160, 160, 3]
    backbone = "mobilenet"
    model_path = "model_data/facenet_mobilenet.pth"

    # 训练
    batch_size = 32  # 小batch size有助于正则化
    Init_Epoch = 0
    Epoch = 80  # 较长训练
    Init_lr = 5e-4  # 较低学习率
    Min_lr = Init_lr * 0.01
    optimizer_type = "adam"
    momentum = 0.9
    weight_decay = 5e-4  # L2正则化
    lr_decay_type = "cos"

    # 正则化
    dropout_keep_prob = 0.5  # dropout比率
    label_smoothing = 0.1  # 标签平滑

    # 剪枝量化
    prune_enabled = True
    prune_sparsity = 0.4  # 40%稀疏度
    prune_start_epoch = 15

    save_period = 5
    save_dir = 'logs_robust'
    num_workers = 4

    # ========== 初始化 ==========
    from utils.utils import seed_everything, get_num_classes, show_config
    from nets.facenet import Facenet
    from nets.facenet_training import get_lr_scheduler, set_optimizer_lr, triplet_loss

    seed_everything(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    num_classes = get_num_classes(annotation_path)
    print(f"类别数: {num_classes}")

    # ========== 模型 ==========
    model = Facenet(
        backbone=backbone,
        num_classes=num_classes,
        dropout_keep_prob=dropout_keep_prob,
        pretrained=False
    )

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

    # ========== 损失函数 ==========
    triplet_loss_fn = triplet_loss()
    ce_loss_fn = LabelSmoothingCrossEntropy(smoothing=label_smoothing)

    # ========== 数据 ==========
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

    # ========== 优化器 ==========
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

    # 数据加载器 - 使用强增强
    train_dataset = StrongAugmentationDataset(input_shape, lines_train, num_classes, random=True)
    val_dataset = StrongAugmentationDataset(input_shape, lines_val, num_classes, random=False)

    gen = DataLoader(
        train_dataset, shuffle=True, batch_size=batch_size // 3, num_workers=num_workers,
        pin_memory=True, drop_last=True, collate_fn=dataset_collate
    )
    gen_val = DataLoader(
        val_dataset, shuffle=False, batch_size=batch_size // 3, num_workers=num_workers,
        pin_memory=True, drop_last=True, collate_fn=dataset_collate
    )

    os.makedirs(save_dir, exist_ok=True)

    # ========== 训练循环 ==========
    print("\n" + "="*50)
    print("开始鲁棒训练 (强正则化 + 剪枝 + 量化)")
    print("="*50)

    model = model.cuda() if Cuda else model
    model.train()

    best_accuracy = 0.0

    for epoch in range(Init_Epoch, Epoch):
        set_optimizer_lr(optimizer, lr_scheduler_func, epoch)

        # 剪枝
        if prune_enabled and epoch >= prune_start_epoch:
            current_sparsity = prune_sparsity * min(1.0, (epoch - prune_start_epoch) / 20)
            if current_sparsity > 0.05:
                print(f"\n>>> Epoch {epoch+1}: 剪枝 (稀疏度: {current_sparsity:.2%})")
                # 对卷积层进行剪枝
                for name, module in model.named_modules():
                    if isinstance(module, nn.Conv2d):
                        weight = module.weight.data.abs()
                        filter_norms = weight.sum(dim=(1, 2, 3))
                        k = int(len(filter_norms) * current_sparsity)
                        if k > 0:
                            threshold = filter_norms.kthvalue(k)[0]
                            mask = filter_norms.gt(threshold).float().view(-1, 1, 1, 1)
                            module.weight.data.mul_(mask)

        # 训练
        total_triple_loss = 0
        total_ce_loss = 0
        total_accuracy = 0

        for iteration, batch in enumerate(gen):
            if iteration >= epoch_step:
                break

            images, labels = batch
            if Cuda:
                images = images.cuda()
                labels = labels.cuda()

            optimizer.zero_grad()

            outputs1, outputs2 = model(images, "train")

            # 损失
            _triplet_loss = triplet_loss_fn(outputs1, batch_size // 3)
            _ce_loss = ce_loss_fn(outputs2, labels)
            _loss = _triplet_loss + _ce_loss

            _loss.backward()
            optimizer.step()

            # 准确率
            accuracy = torch.mean(
                (torch.argmax(F.softmax(outputs2, dim=-1), dim=-1) == labels).float()
            )

            total_triple_loss += _triplet_loss.item()
            total_ce_loss += _ce_loss.item()
            total_accuracy += accuracy.item()

            if iteration % 10 == 0:
                print(f"Epoch {epoch+1}/{Epoch} Iter {iteration}/{epoch_step} "
                      f"Loss: {(_triplet_loss + _ce_loss):.4f} Acc: {accuracy:.4f}")

        # 验证
        model.eval()
        val_total_accuracy = 0
        with torch.no_grad():
            for iteration, batch in enumerate(gen_val):
                if iteration >= epoch_step_val:
                    break
                images, labels = batch
                if Cuda:
                    images = images.cuda()
                    labels = labels.cuda()

                _, outputs2 = model(images, "train")
                accuracy = torch.mean(
                    (torch.argmax(F.softmax(outputs2, dim=-1), dim=-1) == labels).float()
                )
                val_total_accuracy += accuracy.item()

        val_accuracy = val_total_accuracy / epoch_step_val
        model.train()

        print(f"\nEpoch {epoch+1}/{Epoch} 完成")
        print(f"  训练准确率: {total_accuracy / epoch_step:.4f}")
        print(f"  验证准确率: {val_accuracy:.4f}")

        # 保存最佳模型
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            torch.save(model.state_dict(), os.path.join(save_dir, 'best_model.pth'))
            print(f">>> 保存最佳模型: {best_accuracy:.4f}")

        # 定期保存
        if (epoch + 1) % save_period == 0:
            torch.save(model.state_dict(), os.path.join(
                save_dir, f'ep{epoch+1:03d}-acc{val_accuracy:.4f}.pth'
            ))

    # ========== 最终剪枝和量化 ==========
    print("\n" + "="*50)
    print("最终剪枝和量化")
    print("="*50)

    # 最终剪枝
    if prune_enabled:
        print(f"执行最终剪枝 (稀疏度: {prune_sparsity})")
        for name, module in model.named_modules():
            if isinstance(module, nn.Conv2d):
                weight = module.weight.data.abs()
                filter_norms = weight.sum(dim=(1, 2, 3))
                k = int(len(filter_norms) * prune_sparsity)
                if k > 0:
                    threshold = filter_norms.kthvalue(k)[0]
                    mask = filter_norms.gt(threshold).float().view(-1, 1, 1, 1)
                    module.weight.data.mul_(mask)

        torch.save(model.state_dict(), os.path.join(save_dir, 'model_pruned.pth'))

    # 量化
    print("执行动态量化")
    model_quantized = torch.quantization.quantize_dynamic(
        model,
        {nn.Conv2d, nn.Linear},
        dtype=torch.qint8
    )
    torch.save(model_quantized.state_dict(), os.path.join(save_dir, 'model_quantized.pth'))

    # 模型大小比较
    def get_size(path):
        return os.path.getsize(path) / (1024 * 1024) if os.path.exists(path) else 0

    print(f"\n模型大小:")
    print(f"  最佳模型: {get_size(os.path.join(save_dir, 'best_model.pth')):.2f} MB")
    print(f"  剪枝模型: {get_size(os.path.join(save_dir, 'model_pruned.pth')):.2f} MB")
    print(f"  量化模型: {get_size(os.path.join(save_dir, 'model_quantized.pth')):.2f} MB")

    print("\n" + "="*50)
    print(f"训练完成! 最佳准确率: {best_accuracy:.4f}")
    if best_accuracy >= 0.98:
        print("✓ 已达到0.98目标!")
    print("="*50)

    return model_quantized, best_accuracy


if __name__ == "__main__":
    # 需要PIL的ImageEnhance
    try:
        from PIL import ImageEnhance
    except ImportError:
        print("请安装 Pillow: pip install Pillow")

    model, accuracy = train_robust()
