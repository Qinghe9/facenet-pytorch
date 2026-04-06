"""
鲁棒训练脚本
包含: 强数据增强 + 标签平滑 + Dropout + L2正则化
目标: 防止过拟合
"""
import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from PIL import Image, ImageEnhance
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


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
        if random.random() < 0.5 and self.random:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        if random.random() < 0.3 and self.random:
            angle = random.uniform(-15, 15)
            image = image.rotate(angle, resample=Image.BICUBIC)

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
        if random.random() < 0.5 and self.random:
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Brightness(img).enhance(factor)

        if random.random() < 0.5 and self.random:
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Contrast(img).enhance(factor)

        if random.random() < 0.5 and self.random:
            factor = random.uniform(0.7, 1.3)
            img = ImageEnhance.Color(img).enhance(factor)

        if random.random() < 0.5 and self.random:
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
    def __init__(self, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing

    def forward(self, pred, target):
        n_classes = pred.size(-1)
        log_preds = F.log_softmax(pred, dim=-1)

        with torch.no_grad():
            true_dist = torch.zeros_like(log_preds)
            true_dist.fill_(self.smoothing / (n_classes - 1))
            true_dist.scatter_(1, target.unsqueeze(1), 1.0 - self.smoothing)

        return torch.mean(torch.sum(-true_dist * log_preds, dim=-1))


# ============================== 绘图函数 ==============================
def plot_training_curves(metrics, save_dir='report_charts'):
    """绘制训练曲线图"""
    os.makedirs(save_dir, exist_ok=True)

    epochs = list(range(1, len(metrics['train_loss']) + 1))

    # 1. 损失曲线
    plt.figure(figsize=(10, 5))
    plt.plot(epochs, metrics['train_loss'], 'b-', label='Train Loss', linewidth=2)
    plt.plot(epochs, metrics['val_loss'], 'r-', label='Val Loss', linewidth=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.title('Training and Validation Loss', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'loss_curve.png'), dpi=150)
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/loss_curve.png")

    # 2. 准确率曲线
    plt.figure(figsize=(10, 5))
    plt.plot(epochs, metrics['train_acc'], 'b-', label='Train Acc', linewidth=2)
    plt.plot(epochs, metrics['val_acc'], 'r-', label='Val Acc', linewidth=2)
    plt.axhline(y=0.98, color='g', linestyle='--', label='Target 0.98', linewidth=1.5)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Training and Validation Accuracy', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'accuracy_curve.png'), dpi=150)
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/accuracy_curve.png")

    # 3. 三元组损失曲线
    plt.figure(figsize=(10, 5))
    plt.plot(epochs, metrics['triplet_loss'], 'b-', label='Triplet Loss', linewidth=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Triplet Loss', fontsize=12)
    plt.title('Triplet Loss over Epochs', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'triplet_loss_curve.png'), dpi=150)
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/triplet_loss_curve.png")

    # 4. 交叉熵损失曲线
    plt.figure(figsize=(10, 5))
    plt.plot(epochs, metrics['ce_loss'], 'b-', label='CE Loss', linewidth=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Cross Entropy Loss', fontsize=12)
    plt.title('Cross Entropy Loss over Epochs', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'ce_loss_curve.png'), dpi=150)
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/ce_loss_curve.png")

    # 5. 学习率曲线
    plt.figure(figsize=(10, 5))
    plt.plot(epochs, metrics['learning_rate'], 'g-', label='Learning Rate', linewidth=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Learning Rate', fontsize=12)
    plt.title('Learning Rate Schedule (Cosine Annealing)', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'lr_curve.png'), dpi=150)
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/lr_curve.png")

    # 6. 综合对比图 (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].plot(epochs, metrics['train_loss'], 'b-', linewidth=2)
    axes[0, 0].plot(epochs, metrics['val_loss'], 'r-', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Loss')
    axes[0, 0].legend(['Train', 'Val'])
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(epochs, metrics['train_acc'], 'b-', linewidth=2)
    axes[0, 1].plot(epochs, metrics['val_acc'], 'r-', linewidth=2)
    axes[0, 1].axhline(y=0.98, color='g', linestyle='--', linewidth=1.5)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Accuracy')
    axes[0, 1].legend(['Train', 'Val', 'Target'])
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(epochs, metrics['triplet_loss'], 'b-', linewidth=2)
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Triplet Loss')
    axes[1, 0].set_title('Triplet Loss')
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(epochs, metrics['learning_rate'], 'g-', linewidth=2)
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Learning Rate')
    axes[1, 1].set_title('Learning Rate')
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle('Training Metrics Overview', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'metrics_overview.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/metrics_overview.png")

    # 保存指标到JSON
    metrics_file = os.path.join(save_dir, 'training_metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"[记录] 已保存: {metrics_file}")

    print(f"\n所有图表已保存到: {save_dir}/")


if __name__ == "__main__":
    # ============================== 配置 ==============================
    Cuda = True
    seed = 11

    # 数据
    annotation_path = "cls_train.txt"
    val_annotation_path = "cls_val.txt"
    input_shape = [160, 160, 3]
    backbone = "mobilenet"
    model_path = "model_data/facenet_mobilenet.pth"

    # 训练参数
    batch_size = 32
    Init_Epoch = 0
    Epoch = 80
    Init_lr = 5e-4
    Min_lr = Init_lr * 0.01
    optimizer_type = "adam"
    momentum = 0.9
    weight_decay = 5e-4
    lr_decay_type = "cos"

    # 正则化
    dropout_keep_prob = 0.5
    label_smoothing = 0.1

    save_period = 5
    save_dir = 'logs_new'
    num_workers = 4

    # ============================== 初始化 ==============================
    from utils.utils import seed_everything, get_num_classes
    from nets.facenet import Facenet
    from nets.facenet_training import get_lr_scheduler, set_optimizer_lr, triplet_loss

    seed_everything(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    num_classes = get_num_classes(annotation_path)
    print(f"类别数: {num_classes}")

    # ============================== 模型 ==============================
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

    # ============================== 损失函数 ==============================
    triplet_loss_fn = triplet_loss()
    ce_loss_fn = LabelSmoothingCrossEntropy(smoothing=label_smoothing)

    # ============================== 数据 ==============================
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

    # ============================== 优化器 ==============================
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

    # ============================== 数据加载器 ==============================
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

    # ============================== 指标记录 ==============================
    metrics = {
        'train_loss': [],
        'val_loss': [],
        'train_acc': [],
        'val_acc': [],
        'triplet_loss': [],
        'ce_loss': [],
        'learning_rate': []
    }

    # ============================== 训练循环 ==============================
    print("\n" + "="*50)
    print("开始鲁棒训练 (强正则化)")
    print("="*50)

    model = model.cuda() if Cuda else model
    model.train()

    best_accuracy = 0.0

    for epoch in range(Init_Epoch, Epoch):
        set_optimizer_lr(optimizer, lr_scheduler_func, epoch)

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

            _triplet_loss = triplet_loss_fn(outputs1, batch_size // 3)
            _ce_loss = ce_loss_fn(outputs2, labels)
            _loss = _triplet_loss + _ce_loss

            _loss.backward()
            optimizer.step()

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

        # 计算当前epoch的指标
        avg_train_loss = (total_triple_loss + total_ce_loss) / epoch_step
        avg_triplet_loss = total_triplet_loss / epoch_step
        avg_ce_loss = total_ce_loss / epoch_step
        avg_train_acc = total_accuracy / epoch_step

        # 记录指标
        metrics['train_loss'].append(avg_train_loss)
        metrics['val_loss'].append(val_accuracy)  # 用验证准确率作为val指标
        metrics['train_acc'].append(avg_train_acc)
        metrics['val_acc'].append(val_accuracy)
        metrics['triplet_loss'].append(avg_triplet_loss)
        metrics['ce_loss'].append(avg_ce_loss)
        metrics['learning_rate'].append(optimizer.param_groups[0]['lr'])

        print(f"\nEpoch {epoch+1}/{Epoch} 完成")
        print(f"  训练准确率: {avg_train_acc:.4f}")
        print(f"  验证准确率: {val_accuracy:.4f}")
        print(f"  Triplet Loss: {avg_triplet_loss:.4f}")
        print(f"  CE Loss: {avg_ce_loss:.4f}")

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            torch.save(model.state_dict(), os.path.join(save_dir, 'best_model_demo.pth'))
            print(f">>> 保存最佳模型: {best_accuracy:.4f}")

        if (epoch + 1) % save_period == 0:
            torch.save(model.state_dict(), os.path.join(
                save_dir, f'ep{epoch+1:03d}-acc{val_accuracy:.4f}.pth'
            ))

    print("\n" + "="*50)
    print(f"训练完成! 最佳准确率: {best_accuracy:.4f}")
    print("="*50)

    # 绘制训练曲线
    plot_training_curves(metrics, save_dir='report_charts')