"""
配置文件
"""
import os

class Config:
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'face-attendance-secret-key-2024'
    DEBUG = True

    # MySQL数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '123456'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'face_attendance'

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    FACE_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'faces')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

    # 人脸识别模型配置
    FACE_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs_robust', 'best_model.pth')
    FACE_INPUT_SHAPE = [160, 160, 3]
    FACE_BACKBONE = 'mobilenet'
    FACE_THRESHOLD = 0.7  # 人脸比对阈值，越小越严格

    # 考勤配置
    ATTENDANCE_LATE_MINUTES = 15  # 超过多少分钟算迟到
