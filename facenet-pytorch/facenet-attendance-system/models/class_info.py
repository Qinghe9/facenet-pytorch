from models import db
from datetime import datetime

class ClassInfo(db.Model):
    __tablename__ = 'class_info'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(100), nullable=False, index=True)
    grade = db.Column(db.String(20))
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('teacher.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    students = db.relationship('Student', backref='class_info', lazy=True)
    courses = db.relationship('Course', backref='class_info', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'class_name': self.class_name,
            'grade': self.grade,
            'teacher_id': self.teacher_id,
            'teacher_name': self.head_teacher.name if self.head_teacher else None,
            'student_count': len(self.students),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
