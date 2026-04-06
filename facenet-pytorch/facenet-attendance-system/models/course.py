from models import db
from datetime import datetime

class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String(50), nullable=False, index=True)
    course_name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('teacher.id', ondelete='CASCADE'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('class_info.id', ondelete='SET NULL'))
    week_day = db.Column(db.SmallInteger)  # 1-7
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    location = db.Column(db.String(100))
    semester = db.Column(db.String(20))  # 如: 2024-1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    students = db.relationship('CourseStudent', backref='course', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='course', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'course_code': self.course_code,
            'course_name': self.course_name,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'class_id': self.class_id,
            'class_name': self.class_info.class_name if self.class_info else None,
            'week_day': self.week_day,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'semester': self.semester,
            'student_count': len(self.students),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CourseStudent(db.Model):
    __tablename__ = 'course_student'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    course_id = db.Column(db.BigInteger, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='uk_course_student'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_code': self.student.student_code if self.student else None
        }
