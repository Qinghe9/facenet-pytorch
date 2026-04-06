"""
教师管理路由
"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from models import db
from models.teacher import Teacher
from models.class_info import ClassInfo
from models.course import Course, CourseStudent
from models.student import Student
from functools import wraps

teacher_bp = Blueprint('teacher', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'teacher':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/teacher/dashboard')
@login_required
def dashboard():
    """教师仪表盘"""
    teacher_id = session['user_id']

    # 获取统计数据
    my_classes = ClassInfo.query.filter_by(teacher_id=teacher_id).all()
    my_courses = Course.query.filter_by(teacher_id=teacher_id).all()

    # 统计学生总数
    class_ids = [c.id for c in my_classes]
    student_count = Student.query.filter(Student.class_id.in_(class_ids)).count() if class_ids else 0

    return render_template('teacher/dashboard.html',
                           teacher_name=session.get('user_name'),
                           class_count=len(my_classes),
                           course_count=len(my_courses),
                           student_count=student_count)

@teacher_bp.route('/teacher/classes')
@login_required
def list_classes():
    """班级列表页面"""
    classes = ClassInfo.query.all()
    return render_template('teacher/classes.html', classes=classes)

@teacher_bp.route('/api/classes', methods=['GET'])
@login_required
def get_classes():
    """获取班级列表API"""
    classes = ClassInfo.query.all()
    return jsonify({'success': True, 'data': [c.to_dict() for c in classes]})

@teacher_bp.route('/api/classes', methods=['POST'])
@login_required
def create_class():
    """创建班级"""
    data = request.get_json()
    class_name = data.get('class_name')
    grade = data.get('grade')

    if not class_name:
        return jsonify({'success': False, 'message': '班级名称不能为空'})

    class_info = ClassInfo(
        class_name=class_name,
        grade=grade,
        teacher_id=session['user_id']
    )

    db.session.add(class_info)
    db.session.commit()

    return jsonify({'success': True, 'message': '班级创建成功', 'data': class_info.to_dict()})

@teacher_bp.route('/api/classes/<int:class_id>', methods=['PUT'])
@login_required
def update_class(class_id):
    """更新班级"""
    class_info = ClassInfo.query.get(class_id)
    if not class_info:
        return jsonify({'success': False, 'message': '班级不存在'})

    data = request.get_json()
    if 'class_name' in data:
        class_info.class_name = data['class_name']
    if 'grade' in data:
        class_info.grade = data['grade']
    if 'teacher_id' in data:
        class_info.teacher_id = data['teacher_id']

    db.session.commit()
    return jsonify({'success': True, 'message': '更新成功', 'data': class_info.to_dict()})

@teacher_bp.route('/api/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    """删除班级"""
    class_info = ClassInfo.query.get(class_id)
    if not class_info:
        return jsonify({'success': False, 'message': '班级不存在'})

    db.session.delete(class_info)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})

@teacher_bp.route('/teacher/courses')
@login_required
def list_courses():
    """课程列表页面"""
    courses = Course.query.filter_by(teacher_id=session['user_id']).all()
    classes = ClassInfo.query.filter_by(teacher_id=session['user_id']).all()
    return render_template('teacher/courses.html', courses=courses, classes=classes)

@teacher_bp.route('/api/courses', methods=['GET'])
@login_required
def get_courses():
    """获取课程列表API"""
    courses = Course.query.filter_by(teacher_id=session['user_id']).all()
    return jsonify({'success': True, 'data': [c.to_dict() for c in courses]})

@teacher_bp.route('/api/courses', methods=['POST'])
@login_required
def create_course():
    """创建课程"""
    data = request.get_json()

    course = Course(
        course_code=data.get('course_code'),
        course_name=data.get('course_name'),
        teacher_id=session['user_id'],
        class_id=data.get('class_id'),
        week_day=data.get('week_day'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        location=data.get('location'),
        semester=data.get('semester')
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({'success': True, 'message': '课程创建成功', 'data': course.to_dict()})

@teacher_bp.route('/api/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    """更新课程"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': '课程不存在'})

    data = request.get_json()

    if 'course_code' in data:
        course.course_code = data['course_code']
    if 'course_name' in data:
        course.course_name = data['course_name']
    if 'class_id' in data:
        course.class_id = data['class_id']
    if 'week_day' in data:
        course.week_day = data['week_day']
    if 'start_time' in data:
        course.start_time = data['start_time']
    if 'end_time' in data:
        course.end_time = data['end_time']
    if 'location' in data:
        course.location = data['location']
    if 'semester' in data:
        course.semester = data['semester']

    db.session.commit()
    return jsonify({'success': True, 'message': '更新成功', 'data': course.to_dict()})

@teacher_bp.route('/api/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    """删除课程"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': '课程不存在'})

    db.session.delete(course)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})

@teacher_bp.route('/api/courses/<int:course_id>/students', methods=['GET'])
@login_required
def get_course_students(course_id):
    """获取课程学生列表"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': '课程不存在'})

    # 获取班级学生
    if course.class_id:
        students = Student.query.filter_by(class_id=course.class_id).all()
    else:
        # 获取所有已选该课的学生
        cs_list = CourseStudent.query.filter_by(course_id=course_id).all()
        students = [cs.student for cs in cs_list]

    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in students]
    })

@teacher_bp.route('/api/courses/<int:course_id>/students', methods=['POST'])
@login_required
def add_course_student(course_id):
    """添加课程学生"""
    data = request.get_json()
    student_id = data.get('student_id')

    existing = CourseStudent.query.filter_by(
        course_id=course_id,
        student_id=student_id
    ).first()

    if existing:
        return jsonify({'success': False, 'message': '学生已在课程中'})

    cs = CourseStudent(course_id=course_id, student_id=student_id)
    db.session.add(cs)
    db.session.commit()

    return jsonify({'success': True, 'message': '添加成功'})
