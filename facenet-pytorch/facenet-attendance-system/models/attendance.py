from models import db
from datetime import datetime

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_record'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.BigInteger, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_in_type = db.Column(db.String(20), default='camera')  # camera-摄像头, manual-手动
    status = db.Column(db.String(20), nullable=False)  # normal-正常, late-迟到, absent-缺勤, leave-请假
    confidence = db.Column(db.Numeric(5, 4))  # 识别置信度
    face_image_path = db.Column(db.String(255))  # 签到时人脸截图路径
    remarks = db.Column(db.String(255))  # 备注(如迟到原因)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_student_course', 'student_id', 'course_id'),
        db.Index('idx_check_in_time', 'check_in_time'),
        db.Index('idx_course_date', 'course_id', 'check_in_time'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_code': self.student.student_code if self.student else None,
            'course_id': self.course_id,
            'course_name': self.course.course_name if self.course else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_in_type': self.check_in_type,
            'status': self.status,
            'confidence': float(self.confidence) if self.confidence else None,
            'face_image_path': self.face_image_path,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
