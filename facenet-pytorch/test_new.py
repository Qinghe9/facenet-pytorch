"""
模型测试脚本
"""
import os
import json
import numpy as np
import torch
from torch.utils.data import DataLoader

from nets.facenet import Facenet
from utils.dataloader import FacenetDataset, dataset_collate
from utils.utils import get_num_classes

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ============================== 绘图函数 ==============================
def plot_test_results(results, save_dir='report_charts'):
    """绘制测试结果图表"""
    os.makedirs(save_dir, exist_ok=True)

    if not results:
        print("没有测试结果可绘图")
        return

    # 按准确率排序
    results.sort(key=lambda x: x[1], reverse=True)

    model_names = [r[0] for r in results]
    accuracies = [r[1] * 100 for r in results]

    # 1. 准确率柱状图
    plt.figure(figsize=(12, 6))
    colors = ['#2ecc71' if acc >= 92 else '#e74c3c' for acc in accuracies]
    bars = plt.bar(range(len(model_names)), accuracies, color=colors, edgecolor='black', linewidth=1.2)
    plt.axhline(y=98, color='#3498db', linestyle='--', linewidth=2, label='Target 98%')
    plt.axhline(y=92, color='#9b59b6', linestyle='--', linewidth=2, label='Target 92%')

    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Accuracy (%)', fontsize=12)
    plt.title('Model Accuracy Comparison', fontsize=14)
    plt.xticks(range(len(model_names)), model_names, rotation=45, ha='right', fontsize=9)
    plt.legend(fontsize=11)
    plt.grid(True, axis='y', alpha=0.3)

    # 在柱状图上标注数值
    for bar, acc in zip(bars, accuracies):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{acc:.2f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'accuracy_comparison.png'), dpi=150)
    plt.close()
    print(f"[绘图] 已保存: {save_dir}/accuracy_comparison.png")

    # 2. 准确率分布饼图
    success_count = sum(1 for acc in accuracies if acc >= 98)
    partial_count = sum(1 for acc in accuracies if 92 <= acc < 98)
    fail_count = sum(1 for acc in accuracies if acc < 92)

    if len(results) > 1:
        plt.figure(figsize=(8, 8))
        sizes = [success_count, partial_count, fail_count]
        labels = [f'Achieved (≥98%)\n{success_count} models',
                 f'Partial (92-98%)\n{partial_count} models',
                 f'Below Target (<92%)\n{fail_count} models']
        colors_pie = ['#2ecc71', '#f39c12', '#e74c3c']
        explode = (0.05, 0.02, 0.02)

        if sum(sizes) > 0:
            plt.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                   autopct='%1.1f%%', shadow=True, startangle=90)
            plt.title('Test Results Distribution', fontsize=14)
            plt.savefig(os.path.join(save_dir, 'results_distribution.png'), dpi=150)
            plt.close()
            print(f"[绘图] 已保存: {save_dir}/results_distribution.png")

    # 保存测试结果到JSON
    test_results = {
        'models': [{'name': r[0], 'accuracy': r[1]} for r in results],
        'best_model': {'name': results[0][0], 'accuracy': results[0][1]} if results else None,
        'summary': {
            'total_models': len(results),
            'achieved_target': success_count,
            'partial': partial_count,
            'below_target': fail_count
        }
    }

    results_file = os.path.join(save_dir, 'test_results.json')
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"[记录] 已保存: {results_file}")

    print(f"\n所有测试图表已保存到: {save_dir}/")


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
        for _, (images, labels) in enumerate(data_loader):
            images = images.to(device)
            labels = labels.to(device)

            _, outputs = model(images, mode="train")

            _, predicted = torch.max(outputs, 1)
            total_correct += (predicted == labels).sum().item()
            total_samples += labels.size(0)

    accuracy = total_correct / total_samples if total_samples > 0 else 0
    return accuracy


if __name__ == "__main__":
    # ============================== 配置 ==============================
    test_annotation_path = "cls_test.txt"
    val_annotation_path = "cls_val.txt"

    num_classes = get_num_classes("cls_train.txt")
    batch_size = 16
    backbone = "mobilenet"
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    print("="*50)
    print("模型评估")
    print("="*50)
    print(f"类别数: {num_classes}")
    print(f"设备: {device}")

    # 选择测试集
    test_path = test_annotation_path if os.path.exists(test_annotation_path) else val_annotation_path
    print(f"使用测试集: {test_path}")

    with open(test_path, "r", encoding='utf-8') as f:
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

    # ============================== 测试模型 ==============================
    model_dirs = [
        'logs_new',
    ]

    results = []
    for model_dir in model_dirs:
        if not os.path.exists(model_dir):
            print(f"\n目录不存在: {model_dir}")
            continue

        # 查找最佳模型
        best_model_path = os.path.join(model_dir, 'best_model_demo.pth')
        if os.path.exists(best_model_path):
            print(f"\n测试 {model_dir}/best_model_demo.pth ...")
            try:
                model = load_model(best_model_path, num_classes, backbone, device)
                accuracy = evaluate(model, test_loader, device)
                results.append((f'{model_dir}/best_model_demo', accuracy))
                print(f"  准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
            except Exception as e:
                print(f"  加载失败: {e}")

        # 查找所有epoch模型
        for f in os.listdir(model_dir):
            if f.startswith('ep') and f.endswith('.pth') and 'best' not in f:
                model_path = os.path.join(model_dir, f)
                print(f"\n测试 {model_path} ...")
                try:
                    model = load_model(model_path, num_classes, backbone, device)
                    accuracy = evaluate(model, test_loader, device)
                    results.append((f, accuracy))
                    print(f"  准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
                except Exception as e:
                    print(f"  加载失败: {e}")

    # ============================== 打印结果 ==============================
    print("\n" + "="*50)
    print("测试结果总结")
    print("="*50)

    if results:
        results.sort(key=lambda x: x[1], reverse=True)
        for desc, acc in results:
            status = "✓" if acc >= 0.92 else "✗"
            print(f"  {status} {desc}: {acc:.4f} ({acc*100:.2f}%)")

        best_desc, best_acc = results[0]
        print(f"\n最佳模型: {best_desc} ({best_acc:.4f})")

        if best_acc >= 0.92:
            print("✓ 已达到0.92测试准确率目标!")
        else:
            print(f"✗ 未达到0.92目标 (差距: {0.92 - best_acc:.4f})")
    else:
        print("未找到任何模型文件，请先运行训练脚本")

    # 绘制测试结果图表
    plot_test_results(results, save_dir='report_charts')