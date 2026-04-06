"""
考勤管理路由
"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, send_file
from models import db
from models.attendance import AttendanceRecord
from models.course import Course
from models.student import Student
from models.leave import LeaveRecord
from services.attendance_service import AttendanceService
from services.export_service import ExportService
from functools import wraps
from datetime import datetime, date
from io import BytesIO

attendance_bp = Blueprint('attendance', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@attendance_bp.route('/teacher/attendance')
@login_required
def list_attendance():
    """考勤记录页面"""
    if session.get('user_type') != 'teacher':
        return redirect(url_for('auth.login'))

    courses = Course.query.filter_by(teacher_id=session['user_id']).all()
    return render_template('teacher/attendance.html', courses=courses)

@attendance_bp.route('/teacher/reports')
@login_required
def reports():
    """考勤报表页面"""
    if session.get('user_type') != 'teacher':
        return redirect(url_for('auth.login'))

    courses = Course.query.filter_by(teacher_id=session['user_id']).all()
    return render_template('teacher/reports.html', courses=courses)

@attendance_bp.route('/api/attendance', methods=['GET'])
@login_required
def get_attendance():
    """获取考勤记录API"""
    course_id = request.args.get('course_id', type=int)
    student_id = request.args.get('student_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')

    query = AttendanceRecord.query

    if course_id:
        query = query.filter_by(course_id=course_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if start_date:
        query = query.filter(AttendanceRecord.check_in_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AttendanceRecord.check_in_time <= datetime.fromisoformat(end_date))
    if status:
        query = query.filter_by(status=status)

    records = query.order_by(AttendanceRecord.check_in_time.desc()).limit(500).all()

    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in records]
    })

@attendance_bp.route('/api/attendance/<int:record_id>', methods=['PUT'])
@login_required
def update_attendance(record_id):
    """更新考勤记录"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    record = AttendanceRecord.query.get(record_id)
    if not record:
        return jsonify({'success': False, 'message': '记录不存在'})

    data = request.get_json()

    if 'status' in data:
        record.status = data['status']
    if 'remarks' in data:
        record.remarks = data['remarks']

    db.session.commit()

    return jsonify({'success': True, 'message': '更新成功', 'data': record.to_dict()})

@attendance_bp.route('/api/attendance/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取考勤统计API"""
    course_id = request.args.get('course_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not course_id:
        return jsonify({'success': False, 'message': '请选择课程'})

    # 获取课程信息
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': '课程不存在'})

    # 获取课程学生
    if course.class_id:
        students = Student.query.filter_by(class_id=course.class_id).all()
    else:
        cs_list = CourseStudent.query.filter_by(course_id=course_id).all()
        students = [cs.student for cs in cs_list]

    # 计算每个学生的考勤统计
    statistics = []
    for student in students:
        query = AttendanceRecord.query.filter_by(
            student_id=student.id,
            course_id=course_id
        )

        if start_date:
            query = query.filter(AttendanceRecord.check_in_time >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(AttendanceRecord.check_in_time <= datetime.fromisoformat(end_date))

        records = query.all()

        stats = {
            'student_id': student.id,
            'student_name': student.name,
            'student_code': student.student_code,
            'normal': 0,
            'late': 0,
            'absent': 0,
            'leave': 0
        }

        for r in records:
            if r.status in stats:
                stats[r.status] += 1

        total = sum([stats[k] for k in ['normal', 'late', 'absent', 'leave']])
        if total > 0:
            stats['attendance_rate'] = (stats['normal'] + stats['leave']) / total * 100
        else:
            stats['attendance_rate'] = 0

        statistics.append(stats)

    return jsonify({
        'success': True,
        'data': statistics
    })

@attendance_bp.route('/api/attendance/export', methods=['GET'])
@login_required
def export_attendance():
    """导出考勤记录"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    course_id = request.args.get('course_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    export_type = request.args.get('type', 'records')  # records or statistics

    if not course_id:
        return jsonify({'success': False, 'message': '请选择课程'})

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': '课程不存在'})

    # 获取考勤记录
    query = AttendanceRecord.query.filter_by(course_id=course_id)

    if start_date:
        query = query.filter(AttendanceRecord.check_in_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AttendanceRecord.check_in_time <= datetime.fromisoformat(end_date))

    records = query.order_by(AttendanceRecord.check_in_time.desc()).all()

    if export_type == 'records':
        output_path = ExportService.export_attendance_to_excel(course_id, records)
    else:
        # 获取课程学生
        if course.class_id:
            students = Student.query.filter_by(class_id=course.class_id).all()
        else:
            cs_list = CourseStudent.query.filter_by(course_id=course_id).all()
            students = [cs.student for cs in cs_list]

        # 计算统计数据
        statistics = []
        for student in students:
            student_records = [r for r in records if r.student_id == student.id]
            stats = {
                'student_id': student.id,
                'normal': sum(1 for r in student_records if r.status == 'normal'),
                'late': sum(1 for r in student_records if r.status == 'late'),
                'absent': sum(1 for r in student_records if r.status == 'absent'),
                'leave': sum(1 for r in student_records if r.status == 'leave')
            }
            total = sum([stats[k] for k in ['normal', 'late', 'absent', 'leave']])
            stats['attendance_rate'] = (stats['normal'] + stats['leave']) / total * 100 if total > 0 else 0
            statistics.append(stats)

        output_path = ExportService.export_statistics_to_excel(course_id, statistics, students)

    return send_file(output_path, as_attachment=True)

# 学生端考勤查询
@attendance_bp.route('/student/query')
def student_query():
    """学生考勤查询页面"""
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('auth.login'))

    return render_template('student/query.html', student_name=session.get('user_name'))

@attendance_bp.route('/api/student/attendance', methods=['GET'])
def student_attendance():
    """学生获取自己的考勤记录"""
    if 'user_id' not in session or session.get('user_type') != 'student':
        return jsonify({'success': False, 'message': '未登录'})

    student_id = session['user_id']
    course_id = request.args.get('course_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    service = AttendanceService()
    records = service.get_student_attendance(student_id, course_id, start_date, end_date)

    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in records]
    })

@attendance_bp.route('/api/student/courses', methods=['GET'])
def student_courses():
    """学生获取自己的课程"""
    if 'user_id' not in session or session.get('user_type') != 'student':
        return jsonify({'success': False, 'message': '未登录'})

    student_id = session['user_id']
    student = Student.query.get(student_id)

    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})

    # 获取班级课程
    if student.class_id:
        courses = Course.query.filter_by(class_id=student.class_id).all()
    else:
        # 获取学生选修的课程
        cs_list = CourseStudent.query.filter_by(student_id=student_id).all()
        courses = [cs.course for cs in cs_list]

    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in courses]
    })

# 请假管理
@attendance_bp.route('/api/leave', methods=['GET'])
@login_required
def get_leaves():
    """获取请假记录"""
    if session.get('user_type') == 'student':
        leaves = LeaveRecord.query.filter_by(student_id=session['user_id']).all()
    else:
        leaves = LeaveRecord.query.filter_by(teacher_id=session['user_id']).all()

    return jsonify({
        'success': True,
        'data': [l.to_dict() for l in leaves]
    })

@attendance_bp.route('/api/leave', methods=['POST'])
@login_required
def create_leave():
    """创建请假记录"""
    data = request.get_json()

    leave = LeaveRecord(
        student_id=session['user_id'] if session.get('user_type') == 'student' else data.get('student_id'),
        course_id=data.get('course_id'),
        leave_type=data.get('leave_type'),
        start_date=date.fromisoformat(data.get('start_date')),
        end_date=date.fromisoformat(data.get('end_date')),
        reason=data.get('reason'),
        status='pending'
    )

    db.session.add(leave)
    db.session.commit()

    return jsonify({'success': True, 'message': '请假申请已提交', 'data': leave.to_dict()})

@attendance_bp.route('/api/leave/<int:leave_id>/approve', methods=['POST'])
@login_required
def approve_leave(leave_id):
    """审批请假"""
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'message': '无权限'})

    leave = LeaveRecord.query.get(leave_id)
    if not leave:
        return jsonify({'success': False, 'message': '请假记录不存在'})

    data = request.get_json()
    leave.status = data.get('status', 'approved')
    leave.teacher_id = session['user_id']
    leave.approved_at = datetime.now()

    db.session.commit()

    return jsonify({'success': True, 'message': '审批成功', 'data': leave.to_dict()})
