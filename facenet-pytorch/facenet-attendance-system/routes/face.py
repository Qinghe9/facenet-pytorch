"""
人脸识别路由
"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, current_app
from models import db
from models.student import Student
from models.face import FaceImage
from services.face_service import FaceRecognitionService, FaceDatabase
from utils.face_detector import FaceDetector
from config import Config
import os
import json
import base64
import numpy as np
from PIL import Image
import cv2
from datetime import datetime
from functools import wraps

face_bp = Blueprint('face', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# 初始化人脸识别服务（延迟加载）
_face_service = None
_face_database = None

def get_face_service():
    global _face_service
    if _face_service is None:
        config = Config()
        _face_service = FaceRecognitionService(
            model_path=config.FACE_MODEL_PATH,
            input_shape=config.FACE_INPUT_SHAPE,
            backbone=config.FACE_BACKBONE,
            cuda=True
        )
    return _face_service

def get_face_database():
    global _face_database
    if _face_database is None:
        _face_database = FaceDatabase()
        # 从数据库加载所有人脸特征
        students = Student.query.filter(Student.face_feature.isnot(None)).all()
        _face_database.load_from_students(students)
    return _face_database

# 教师端人脸管理页面
@face_bp.route('/teacher/face')
@login_required
def face_management():
    """人脸管理页面"""
    if session.get('user_type') != 'teacher':
        return redirect(url_for('auth.login'))
    return render_template('face/register.html')

# 学生端人脸采集页面
@face_bp.route('/student/face/capture')
@login_required
def face_capture_page():
    """人脸采集页面"""
    return render_template('face/capture.html')

# 教师端人脸采集页面
@face_bp.route('/teacher/face/capture/<int:student_id>')
@login_required
def teacher_face_capture(student_id):
    """教师端人脸采集"""
    if session.get('user_type') != 'teacher':
        return redirect(url_for('auth.login'))

    student = Student.query.get(student_id)
    if not student:
        return "学生不存在", 404

    return render_template('face/capture.html', student=student, is_teacher=True)

# 获取学生的人脸采集状态
@face_bp.route('/api/face/student/<int:student_id>/status')
@login_required
def get_face_status(student_id):
    """获取学生人脸采集状态"""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    # 获取该学生的人脸图片数量
    face_count = FaceImage.query.filter_by(student_id=student_id).count()

    return jsonify({
        'success': True,
        'data': {
            'student_id': student_id,
            'student_name': student.name,
            'student_code': student.student_code,
            'face_count': face_count,
            'face_registered': student.face_count > 0,
            'db_face_count': student.face_count
        }
    })

# 上传人脸图片并提取特征
@face_bp.route('/api/face/upload', methods=['POST'])
@login_required
def upload_face():
    """上传人脸图片"""
    data = request.get_json()

    if not data or 'image' not in data or 'student_id' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'})

    student_id = data['student_id']
    image_data = data['image']

    # 解析base64图片
    try:
        # 移除data URL前缀
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'success': False, 'message': '图片解析失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'图片解析错误: {str(e)}'})

    # 检测人脸
    detector = FaceDetector()
    faces = detector.detect_faces(img)

    if len(faces) == 0:
        return jsonify({'success': False, 'message': '未检测到人脸'})

    if len(faces) > 1:
        return jsonify({'success': False, 'message': '检测到多个人脸，请确保只有一人在画面中'})

    # 裁剪人脸
    face_rect = faces[0]
    face_img = detector.crop_face(img, face_rect)

    # 保存人脸图片
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    # 创建存储目录
    faces_dir = os.path.join(current_app.root_path, 'uploads', 'faces', str(student_id))
    os.makedirs(faces_dir, exist_ok=True)

    # 保存图片
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    img_filename = f"{student_id}_{timestamp}.jpg"
    img_path = os.path.join(faces_dir, img_filename)
    cv2.imwrite(img_path, face_img)

    # 提取人脸特征
    face_service = get_face_service()
    try:
        face_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        feature = face_service.extract_feature(face_pil)
    except Exception as e:
        os.remove(img_path)
        return jsonify({'success': False, 'message': f'特征提取失败: {str(e)}'})

    # 保存人脸图片记录
    face_image = FaceImage(
        student_id=student_id,
        image_path=img_path,
        feature=json.dumps(feature.tolist())
    )
    db.session.add(face_image)

    # 更新学生的已注册人脸数量
    student.face_count = FaceImage.query.filter_by(student_id=student_id).count()

    # 更新学生的人脸特征集合
    all_features = [json.loads(f.feature) for f in FaceImage.query.filter_by(student_id=student_id).all()]
    student.set_face_features(all_features)

    db.session.commit()

    # 更新内存中的人脸数据库
    global _face_database
    if _face_database:
        _face_database.load_from_students([student])

    return jsonify({
        'success': True,
        'message': '人脸上传成功',
        'data': {
            'face_count': student.face_count,
            'confidence': float(np.random.uniform(0.95, 0.99))  # 模拟置信度
        }
    })

# 注册学生人脸（从已上传的图片中提取特征）
@face_bp.route('/api/face/register/<int:student_id>', methods=['POST'])
@login_required
def register_face(student_id):
    """注册学生人脸特征"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    # 获取该学生的所有人脸图片
    face_images = FaceImage.query.filter_by(student_id=student_id).all()

    if len(face_images) < 3:
        return jsonify({
            'success': False,
            'message': f'人脸图片不足，需要至少3张，当前{len(face_images)}张'
        })

    # 提取所有特征
    features = []
    for face_img in face_images:
        if os.path.exists(face_img.image_path):
            try:
                img = cv2.imread(face_img.image_path)
                if img is not None:
                    face_service = get_face_service()
                    face_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    feature = face_service.extract_feature(face_pil)
                    features.append(feature.tolist())
            except Exception as e:
                print(f"Error processing face image: {e}")

    if len(features) < 3:
        return jsonify({
            'success': False,
            'message': f'有效人脸特征不足，需要至少3个，当前{len(features)}个'
        })

    # 保存特征到学生表
    student.set_face_features(features)
    student.face_count = len(features)
    db.session.commit()

    # 更新内存中的人脸数据库
    global _face_database
    if _face_database:
        _face_database.load_from_students([student])

    return jsonify({
        'success': True,
        'message': '人脸注册成功',
        'data': {
            'face_count': len(features)
        }
    })

# 人脸识别签到
@face_bp.route('/api/face/recognize', methods=['POST'])
def recognize_face():
    """人脸识别签到"""
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': '缺少图片数据'})

    image_data = data['image']
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'success': False, 'message': '缺少课程ID'})

    # 解析图片
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'success': False, 'message': '图片解析失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'图片解析错误: {str(e)}'})

    # 检测人脸
    detector = FaceDetector()
    faces = detector.detect_faces(img)

    if len(faces) == 0:
        return jsonify({'success': False, 'message': '未检测到人脸'})
    if len(faces) > 1:
        return jsonify({'success': False, 'message': '检测到多个人脸，请确保只有一人在画面中'})

    # 提取特征
    face_rect = faces[0]
    face_img = detector.crop_face(img, face_rect)

    face_service = get_face_service()
    try:
        face_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        capture_feature = face_service.extract_feature(face_pil)
    except Exception as e:
        return jsonify({'success': False, 'message': f'特征提取失败: {str(e)}'})

    # 在人脸数据库中查找匹配
    face_database = get_face_database()

    best_match_id = None
    best_similarity = 0.0

    for student_id, feature in face_database.features:
        matches, cos_sim, _ = face_database.compare(capture_feature, feature, threshold=0.7)
        if matches and cos_sim > best_similarity:
            best_match_id = student_id
            best_similarity = cos_sim

    if best_match_id is None:
        return jsonify({
            'success': False,
            'message': '未找到匹配的人脸，请先注册人脸'
        })

    # 获取学生信息
    student = Student.query.get(best_match_id)
    if not student:
        return jsonify({'success': False, 'message': '学生信息不存在'})

    # 保存签到图片
    check_in_dir = os.path.join(current_app.root_path, 'uploads', 'checkin')
    os.makedirs(check_in_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    checkin_path = os.path.join(check_in_dir, f"{student.student_code}_{timestamp}.jpg")
    cv2.imwrite(checkin_path, face_img)

    # 记录考勤
    from services.attendance_service import AttendanceService
    service = AttendanceService()
    record, msg = service.record_attendance(
        student_id=best_match_id,
        course_id=course_id,
        check_in_type='camera',
        confidence=best_similarity,
        face_image_path=checkin_path
    )

    if record is None:
        return jsonify({'success': False, 'message': msg})

    return jsonify({
        'success': True,
        'message': '签到成功',
        'data': {
            'student_id': student.id,
            'student_code': student.student_code,
            'student_name': student.name,
            'status': record.status,
            'confidence': float(best_similarity),
            'check_in_time': record.check_in_time.isoformat()
        }
    })

# 删除学生人脸
@face_bp.route('/api/face/student/<int:student_id>', methods=['DELETE'])
@login_required
def delete_face(student_id):
    """删除学生人脸"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    # 删除人脸图片文件
    face_images = FaceImage.query.filter_by(student_id=student_id).all()
    for face_img in face_images:
        if os.path.exists(face_img.image_path):
            try:
                os.remove(face_img.image_path)
            except:
                pass
        db.session.delete(face_img)

    # 清空学生的人脸特征
    student.face_feature = None
    student.face_count = 0

    db.session.commit()

    # 更新内存中的人脸数据库
    global _face_database
    if _face_database:
        _face_database.load_from_students(Student.query.filter(Student.face_feature.isnot(None)).all())

    return jsonify({'success': True, 'message': '人脸删除成功'})
