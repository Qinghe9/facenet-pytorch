"""
人脸识别考勤系统 - Flask应用入口
"""
import os
from flask import Flask, render_template, session, jsonify
from flask_cors import CORS
from models import db
from config import Config

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    CORS(app)
    db.init_app(app)

    # 确保上传目录存在
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('FACE_IMAGES_FOLDER', 'uploads/faces'), exist_ok=True)

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.teacher import teacher_bp
    from routes.attendance import attendance_bp
    from routes.face import face_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(face_bp)

    # 主页
    @app.route('/')
    def index():
        return render_template('login.html')

    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Face Attendance System is running'})

    # 初始化数据库
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
