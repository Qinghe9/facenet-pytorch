"""
学生管理路由
"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from models import db
from models.student import Student
from models.class_info import ClassInfo
from functools import wraps

student_bp = Blueprint('student', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/teacher/students')
@login_required
def list_students():
    """学生列表页面"""
    if session.get('user_type') != 'teacher':
        return redirect(url_for('auth.login'))

    class_id = request.args.get('class_id', type=int)
    search = request.args.get('search', '')

    query = Student.query
    if class_id:
        query = query.filter_by(class_id=class_id)
    if search:
        query = query.filter(
            db.or_(
                Student.name.like(f'%{search}%'),
                Student.student_code.like(f'%{search}%')
            )
        )

    students = query.order_by(Student.created_at.desc()).all()
    classes = ClassInfo.query.all()

    return render_template('teacher/students.html',
                           students=students,
                           classes=classes,
                           current_class_id=class_id,
                           search=search)

@student_bp.route('/api/students', methods=['GET'])
@login_required
def get_students():
    """获取学生列表API"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    class_id = request.args.get('class_id', type=int)

    query = Student.query
    if class_id:
        query = query.filter_by(class_id=class_id)

    students = query.all()
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in students]
    })

@student_bp.route('/api/students', methods=['POST'])
@login_required
def create_student():
    """创建学生"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    data = request.get_json()
    student_code = data.get('student_code')
    name = data.get('name')
    class_id = data.get('class_id')
    password = data.get('password', '123456')

    if not student_code or not name:
        return jsonify({'success': False, 'message': '学号和姓名不能为空'})

    # 检查学号是否已存在
    if Student.query.filter_by(student_code=student_code).first():
        return jsonify({'success': False, 'message': '学号已存在'})

    student = Student(
        student_code=student_code,
        name=name,
        class_id=class_id,
        phone=data.get('phone'),
        email=data.get('email')
    )
    student.set_password(password)

    db.session.add(student)
    db.session.commit()

    return jsonify({'success': True, 'message': '学生创建成功', 'data': student.to_dict()})

@student_bp.route('/api/students/<int:student_id>', methods=['GET'])
@login_required
def get_student(student_id):
    """获取学生信息"""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    return jsonify({'success': True, 'data': student.to_dict(include_feature=True)})

@student_bp.route('/api/students/<int:student_id>', methods=['PUT'])
@login_required
def update_student(student_id):
    """更新学生信息"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    data = request.get_json()

    if 'name' in data:
        student.name = data['name']
    if 'class_id' in data:
        student.class_id = data['class_id']
    if 'phone' in data:
        student.phone = data['phone']
    if 'email' in data:
        student.email = data['email']
    if 'status' in data:
        student.status = data['status']
    if 'password' in data and data['password']:
        student.set_password(data['password'])

    db.session.commit()

    return jsonify({'success': True, 'message': '更新成功', 'data': student.to_dict()})

@student_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """删除学生"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    # 删除学生的人脸特征
    student.face_feature = None
    student.face_count = 0

    db.session.delete(student)
    db.session.commit()

    return jsonify({'success': True, 'message': '删除成功'})
