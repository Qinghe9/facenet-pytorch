import torch
import onnx
import onnxruntime as ort
import numpy as np
from facenet_pytorch import InceptionResnetV1

def convert_to_onnx(model_path, onnx_path, input_shape=(1, 3, 160, 160)):
    """将FaceNet模型转换为ONNX格式（Windows 专用修复）"""
    # 1. 创建模型实例（不使用预训练下载）
    print(f"加载预训练模型: {model_path}")
    model = InceptionResnetV1(
        pretrained=None  # 不下载预训练权重，避免网络问题
    ).eval()
    
    # 2. 从模型路径加载权重（指定在CPU上加载）
    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
    
    # 3. 移除 classifier 权重（如果存在）
    if 'classifier.weight' in state_dict:
        del state_dict['classifier.weight']
        del state_dict['classifier.bias']
    
    # 4. 加载微调后的权重
    model.load_state_dict(state_dict, strict=False)
    
    # 5. 创建示例输入
    dummy_input = torch.randn(input_shape, requires_grad=True)
    
    # 6. 设置动态轴
    dynamic_axes = {
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    }
    
    # 7. 导出到ONNX
    print(f"开始转换为ONNX格式，输出文件: {onnx_path}")
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=13,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes=dynamic_axes
    )
    
    print(f"ONNX转换成功! 模型已保存至: {onnx_path}")
    print(f"输入形状: {input_shape}, 输出形状: {model(dummy_input).shape}")
    
    # 8. 验证ONNX模型
    try:
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        print("ONNX模型验证通过!")
    except Exception as e:
        print(f"ONNX模型验证失败: {e}")
    
    return onnx_path

if __name__ == "__main__":
    # 配置参数
    PRETRAINED_MODEL_PATH = "model_data/facenet_mobilenet.pth"
    ONNX_MODEL_PATH = "model_data/facenet_mobile.onnx"
    
    # 确保目录存在
    import os
    os.makedirs("model_data", exist_ok=True)
    
    # 执行转换
    convert_to_onnx(
        model_path=PRETRAINED_MODEL_PATH,
        onnx_path=ONNX_MODEL_PATH,
        input_shape=(1, 3, 160, 160)
    )