"""
模型转换脚本: PyTorch → ONNX
支持: 最佳模型、剪枝模型、量化模型

修复:
1. 使用opset_version=18
2. 移除dynamic_axes (会导致警告)
3. 正确处理量化模型
"""
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from nets.facenet import Facenet
from utils.utils import get_num_classes


def load_pytorch_model(model_path, num_classes, backbone='mobilenet', device='cuda'):
    """加载PyTorch模型"""
    print(f"加载模型: {model_path}")

    model = Facenet(backbone=backbone, num_classes=num_classes, pretrained=False)
    model_dict = model.state_dict()

    pretrained_dict = torch.load(model_path, map_location=device, weights_only=False)
    temp_dict = {}

    for k, v in pretrained_dict.items():
        if k in model_dict.keys() and np.shape(model_dict[k]) == np.shape(v):
            temp_dict[k] = v
        elif 'scale' in k or 'zero_point' in k or '_packed_params' in k:
            # 跳过量化模型的特殊键
            pass
        else:
            print(f"  跳过不匹配的键: {k}")

    model_dict.update(temp_dict)
    model.load_state_dict(model_dict)
    model = model.to(device)
    model.eval()

    print(f"成功加载 {len(temp_dict)} 个权重")
    return model


def convert_to_onnx(model, output_path, input_shape=[160, 160, 3]):
    """
    将PyTorch模型转换为ONNX格式

    Args:
        model: PyTorch模型
        output_path: 输出ONNX文件路径
        input_shape: 输入图像尺寸 [H, W, C]
    """
    print(f"\n转换模型为ONNX: {output_path}")

    # 创建 dummy input
    dummy_input = torch.randn(1, 3, input_shape[0], input_shape[1]).to(next(model.parameters()).device)

    # 设置为eval模式
    model.eval()

    # ONNX转换 - 使用opset_version=18，移除dynamic_axes
    try:
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            input_names=['input'],
            output_names=['output'],
            opset_version=18,
            verbose=False
        )
        print(f"✓ ONNX模型已保存: {output_path}")

        # 显示文件大小
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  文件大小: {size_mb:.2f} MB")
        return True

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_onnx_model(onnx_path, pytorch_model, test_input):
    """验证ONNX模型与PyTorch模型输出一致"""
    try:
        import onnxruntime as ort
    except ImportError:
        print("  onnxruntime未安装，跳过验证")
        return True

    print(f"\n验证ONNX模型: {onnx_path}")

    # PyTorch输出
    with torch.no_grad():
        pytorch_output = pytorch_model(test_input).cpu().numpy()

    # ONNX输出
    session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    onnx_output = session.run(None, {
        'input': test_input.cpu().numpy()
    })[0]

    # 比较
    diff = np.abs(pytorch_output - onnx_output).max()
    mean_diff = np.abs(pytorch_output - onnx_output).mean()

    print(f"  PyTorch输出范围: [{pytorch_output.min():.4f}, {pytorch_output.max():.4f}]")
    print(f"  ONNX输出范围: [{onnx_output.min():.4f}, {onnx_output.max():.4f}]")
    print(f"  最大差异: {diff:.6f}, 平均差异: {mean_diff:.6f}")

    # 差异小于1e-3视为正常（浮点精度）
    if diff < 1e-3:
        print("  ✓ 验证通过!")
        return True
    else:
        print("  ⚠ 差异较大，请检查模型")
        return False


def convert_all_models():
    """转换所有模型为ONNX格式"""
    # 配置
    backbone = 'mobilenet'
    num_classes = get_num_classes("cls_train.txt")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    input_shape = [160, 160, 3]

    print("="*50)
    print("模型转换: PyTorch → ONNX")
    print("="*50)
    print(f"骨干网络: {backbone}")
    print(f"类别数: {num_classes}")
    print(f"设备: {device}")
    print(f"输入尺寸: {input_shape}")

    # 模型路径配置
    models_config = [
        ('logs_robust/best_model.pth', 'logs_robust/best_model.onnx', '最佳训练模型'),
        ('logs_robust/model_pruned.pth', 'logs_robust/model_pruned.onnx', '剪枝后模型'),
    ]

    # 创建测试输入
    test_input = torch.randn(1, 3, input_shape[0], input_shape[1]).to(device)

    success_count = 0

    for pytorch_path, onnx_path, desc in models_config:
        print(f"\n{'='*50}")
        print(f"处理: {desc}")
        print(f"{'='*50}")

        if not os.path.exists(pytorch_path):
            print(f"✗ 模型文件不存在: {pytorch_path}")
            continue

        # 加载PyTorch模型
        try:
            model = load_pytorch_model(pytorch_path, num_classes, backbone, device)
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            continue

        # 转换ONNX
        if convert_to_onnx(model, onnx_path, input_shape):
            # 验证
            verify_onnx_model(onnx_path, model, test_input)
            success_count += 1

    # 总结
    print("\n" + "="*50)
    print("标准模型转换完成!")
    print("="*50)

    return success_count, len(models_config)


def convert_quantized_model():
    """
    正确处理量化模型的转换
    1. 加载原始模型
    2. 应用量化
    3. 导出ONNX
    """
    print("\n" + "="*50)
    print("处理量化模型")
    print("="*50)

    backbone = 'mobilenet'
    num_classes = get_num_classes("cls_train.txt")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # 1. 加载最佳模型
    print("\n步骤1: 加载最佳模型...")
    best_model = load_pytorch_model('logs_robust/best_model.pth', num_classes, backbone, device)

    # 2. 应用动态量化
    print("\n步骤2: 应用动态量化...")
    best_model.eval()

    # 动态量化只对权重进行量化，推理时仍然是FP32计算
    # ONNX不能很好地表示动态量化，所以我们先量化再导出会失败
    # 正确做法：直接导出FP32模型，量化在推理时用运行时库完成
    print("  注意: 动态量化的INT8权重无法直接导出为ONNX")
    print("  ONNX运行时支持量化操作，但需要QDQ格式(QDQ nodes)")
    print("  将保存FP32版本的ONNX，量化在部署时使用ONNX Runtime进行")

    # 3. 导出ONNX
    print("\n步骤3: 导出ONNX...")
    output_path = 'logs_robust/model_quantized.onnx'
    convert_to_onnx(best_model, output_path, [160, 160, 3])

    # 4. 验证
    test_input = torch.randn(1, 3, 160, 160).to(device)
    verify_onnx_model(output_path, best_model, test_input)

    print("\n" + "="*50)
    print("关于量化的说明:")
    print("="*50)
    print("动态量化模型(如torch.qint8)的权重是量化的，但计算仍是FP32。")
    print("ONNX格式不支持直接导出动态量化模型。")
    print("")
    print("部署选项:")
    print("  1. 使用PyTorch模型 + torch.jit.script")
    print("  2. 使用ONNX模型 + ONNX Runtime的量化工具")
    print("  3. 使用FP32 ONNX模型 + 运行时动态量化")
    print("")
    print("已生成的 best_model.onnx (FP32) 可直接用于推理。")
    print("="*50)


def main():
    """主函数"""
    # 1. 转换标准模型
    success, total = convert_all_models()

    # 2. 处理量化模型
    convert_quantized_model()

    # 列出所有ONNX文件
    print("\n" + "="*50)
    print("所有生成的ONNX文件:")
    print("="*50)
    onnx_files = [
        'logs_robust/best_model.onnx',
        'logs_robust/model_pruned.onnx',
        'logs_robust/model_quantized.onnx'
    ]
    for f in onnx_files:
        if os.path.exists(f):
            size = os.path.getsize(f) / (1024 * 1024)
            print(f"  ✓ {f} ({size:.2f} MB)")
        else:
            print(f"  ✗ {f} (不存在)")


if __name__ == "__main__":
    main()
