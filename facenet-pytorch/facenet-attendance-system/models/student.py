from models import db
from datetime import datetime
import bcrypt
import json

class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('class_info.id', ondelete='SET NULL'))
    password = db.Column(db.String(255), default='123456')
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    face_feature = db.Column(db.Text)  # JSON格式存储人脸特征
    face_count = db.Column(db.Integer, default=0)
    status = db.Column(db.SmallInteger, default=1)  # 0-禁用, 1-正常
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)
    leave_records = db.relationship('LeaveRecord', backref='student', lazy=True)
    course_students = db.relationship('CourseStudent', backref='student', lazy=True)

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def get_face_features(self):
        if self.face_feature:
            return json.loads(self.face_feature)
        return []

    def set_face_features(self, features):
        self.face_feature = json.dumps(features)

    def to_dict(self, include_feature=False):
        data = {
            'id': self.id,
            'student_code': self.student_code,
            'name': self.name,
            'class_id': self.class_id,
            'class_name': self.class_info.class_name if self.class_info else None,
            'phone': self.phone,
            'email': self.email,
            'face_count': self.face_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_feature:
            data['face_feature'] = self.get_face_features()
        return data
