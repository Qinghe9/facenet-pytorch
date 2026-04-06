"""
认证路由
"""
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models.teacher import Teacher
from models.student import Student

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type', 'teacher')  # teacher or student

    if not username or not password:
        return jsonify({'success': False, 'message': '请输入用户名和密码'})

    if user_type == 'teacher':
        user = Teacher.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_type'] = 'teacher'
            session['user_name'] = user.name
            return jsonify({'success': True, 'message': '登录成功', 'redirect': '/teacher/dashboard'})
    else:
        user = Student.query.filter_by(student_code=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_type'] = 'student'
            session['user_name'] = user.name
            session['student_code'] = user.student_code
            return jsonify({'success': True, 'message': '登录成功', 'redirect': '/student/query'})

    return jsonify({'success': False, 'message': '用户名或密码错误'})

@auth_bp.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/check_session')
def check_session():
    """检查会话状态"""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user_type': session.get('user_type'),
            'user_name': session.get('user_name')
        })
    return jsonify({'logged_in': False})
