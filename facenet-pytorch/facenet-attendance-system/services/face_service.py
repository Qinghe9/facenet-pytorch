"""
人脸识别服务
使用预训练的FaceNet模型进行人脸特征提取和比对
"""
import os
import sys
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
import cv2
import json

# 添加上层目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nets.facenet import Facenet as FacenetModel
from utils.face_detector import FaceDetector

# 归一化处理
def preprocess_input(x):
    x = x.astype(np.float32)
    x /= 255.0
    return x

def resize_image(image, size, letterbox_image=True):
    """调整图片大小"""
    if isinstance(image, Image.Image):
        image = np.array(image)

    h, w = size
    ih, iw = image.shape[:2]

    if letterbox_image:
        scale = min(w / iw, h / ih)
        nw = int(iw * scale)
        nh = int(ih * scale)

        image = cv2.resize(image, (nw, nh))
        new_image = np.ones((h, w, 3), dtype=np.uint8) * 128

        top = (h - nh) // 2
        left = (w - nw) // 2
        new_image[top:top + nh, left:left + nw] = image
        return Image.fromarray(new_image)
    else:
        return Image.fromarray(cv2.resize(image, (w, h)))


class FaceRecognitionService:
    """人脸识别服务"""

    def __init__(self, model_path, input_shape=[160, 160, 3], backbone='mobilenet', cuda=True):
        self.model_path = model_path
        self.input_shape = input_shape
        self.backbone = backbone
        self.cuda = cuda
        self.face_detector = FaceDetector()

        # 尝试多个可能的路径
        possible_paths = [
            model_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', model_path),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), model_path),
        ]

        actual_path = None
        for p in possible_paths:
            full_path = os.path.abspath(p)
            if os.path.exists(full_path):
                actual_path = full_path
                break

        if actual_path is None:
            print(f"Warning: Model file not found at {model_path}")
            print(f"Searched paths: {possible_paths}")
            self.model = None
            return

        print(f"Loading model from: {actual_path}")

        device = torch.device('cuda' if torch.cuda.is_available() and cuda else 'cpu')
        self.net = FacenetModel(backbone=self.backbone, mode="predict").eval()
        self.net.load_state_dict(torch.load(actual_path, map_location=device), strict=False)

        if cuda and torch.cuda.is_available():
            self.net = torch.nn.DataParallel(self.net)
            self.net = self.net.cuda()

        self.device = device

    def extract_feature(self, image):
        """
        从图片中提取人脸特征
        返回特征向量
        """
        if self.model is None:
            raise Exception("Model not loaded")

        if isinstance(image, str):
            image = Image.open(image)

        # 调整图片大小
        image = resize_image(image, [self.input_shape[1], self.input_shape[0]], letterbox_image=True)

        # 预处理
        image = preprocess_input(np.array(image, np.float32))
        image = np.transpose(image, (2, 0, 1))
        photo = torch.from_numpy(np.expand_dims(image, 0))

        if self.cuda and torch.cuda.is_available():
            photo = photo.cuda()

        # 提取特征
        with torch.no_grad():
            output = self.net(photo).cpu().numpy()

        return output.flatten()

    def extract_face_feature(self, image):
        """
        检测人脸并提取特征
        如果图片中有多个人脸，返回最大的那个
        """
        if isinstance(image, Image.Image):
            image = np.array(image)

        # 检测人脸
        faces = self.face_detector.detect_faces(image)

        if len(faces) == 0:
            return None, None

        # 获取最大的人脸
        largest_idx = max(range(len(faces)), key=lambda i: faces[i][2] * faces[i][3])
        face_rect = faces[largest_idx]

        # 裁剪人脸
        face_img = self.face_detector.crop_face(image, face_rect)
        face_img = Image.fromarray(face_img)

        try:
            feature = self.extract_feature(face_img)
            return feature, face_rect
        except Exception as e:
            print(f"Error extracting face feature: {e}")
            return None, face_rect

    def compare_faces(self, feature1, feature2, threshold=0.7):
        """
        比较两个人脸特征
        返回是否匹配和相似度
        """
        if feature1 is None or feature2 is None:
            return False, 0.0

        # 计算余弦相似度
        cos_sim = np.dot(feature1, feature2) / (np.linalg.norm(feature1) * np.linalg.norm(feature2))

        # 计算欧氏距离
        euclidean_dist = np.linalg.norm(feature1 - feature2)

        # 转换为相似度 (距离越小，相似度越高)
        # 使用指数衰减: sim = exp(-dist / scale)
        similarity = np.exp(-euclidean_dist / 0.5)

        matches = euclidean_dist < threshold

        return matches, float(cos_sim), float(euclidean_dist)

    def find_matching_student(self, capture_face_feature, registered_features, threshold=0.7):
        """
        在已注册的人脸特征列表中找到匹配的学生
        registered_features: [(student_id, feature), ...]
        返回匹配的学生ID和相似度
        """
        best_match = None
        best_similarity = 0.0
        best_distance = float('inf')

        for student_id, feature in registered_features:
            matches, cos_sim, euclidean_dist = self.compare_faces(
                capture_face_feature, feature, threshold
            )
            if matches and cos_sim > best_similarity:
                best_match = student_id
                best_similarity = cos_sim
                best_distance = euclidean_dist

        return best_match, best_similarity, best_distance


class FaceDatabase:
    """人脸特征数据库管理"""

    def __init__(self):
        self.features = []  # [(student_id, feature), ...]

    def add_feature(self, student_id, feature):
        """添加人脸特征"""
        self.features.append((student_id, feature))

    def load_from_students(self, students):
        """
        从学生列表加载人脸特征
        students: Student模型列表
        """
        self.features = []
        for student in students:
            if student.face_feature:
                try:
                    features = json.loads(student.face_feature)
                    for feature in features:
                        self.add_feature(student.id, np.array(feature))
                except Exception as e:
                    print(f"Error loading features for student {student.id}: {e}")

    def find_match(self, capture_feature, threshold=0.7):
        """找到匹配的学生ID"""
        for student_id, feature in self.features:
            matches, cos_sim, _ = self.compare(capture_feature, feature, threshold)
            if matches:
                return student_id, cos_sim
        return None, 0.0

    def compare(self, feature1, feature2, threshold=0.7):
        """比较两个特征"""
        if feature1 is None or feature2 is None:
            return False, 0.0, float('inf')

        cos_sim = np.dot(feature1, feature2) / (np.linalg.norm(feature1) * np.linalg.norm(feature2))
        euclidean_dist = np.linalg.norm(feature1 - feature2)
        matches = euclidean_dist < threshold

        return matches, float(cos_sim), float(euclidean_dist)
