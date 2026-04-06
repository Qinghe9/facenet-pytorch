"""
人脸检测工具类
使用OpenCV进行人脸检测
"""
import cv2
import numpy as np
from PIL import Image

class FaceDetector:
    def __init__(self):
        # 加载OpenCV自带的人脸检测器
        # HAAR级联分类器
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        # 备用的人脸检测器
        self.face_cascade_alt2 = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
        )

    def detect_faces(self, image):
        """
        检测图片中的人脸
        返回人脸区域列表 [(x, y, w, h), ...]
        """
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 使用级联分类器检测人脸
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) == 0:
            # 尝试使用备用分类器
            faces = self.face_cascade_alt2.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

        return faces

    def get_largest_face(self, image):
        """获取最大的一个人脸"""
        faces = self.detect_faces(image)
        if len(faces) == 0:
            return None
        # 返回最大的脸（按面积）
        largest = max(faces, key=lambda f: f[2] * f[3])
        return largest

    def crop_face(self, image, face_rect, margin=0.2):
        """
        裁剪人脸区域
        face_rect: (x, y, w, h)
        margin: 扩展边距比例
        """
        x, y, w, h = face_rect
        img_h, img_w = image.shape[:2]

        # 添加边距
        margin_x = int(w * margin)
        margin_y = int(h * margin)

        x1 = max(0, x - margin_x)
        y1 = max(0, y - margin_y)
        x2 = min(img_w, x + w + margin_x)
        y2 = min(img_h, y + h + margin_y)

        if isinstance(image, Image.Image):
            return image.crop((x1, y1, x2, y2))
        else:
            return image[y1:y2, x1:x2]

    def draw_faces(self, image, faces, labels=None):
        """在图片上绘制人脸框"""
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        img = image.copy()

        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if labels and i < len(labels):
                cv2.putText(img, labels[i], (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return img
