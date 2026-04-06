from models import db
from datetime import datetime

class LeaveRecord(db.Model):
    __tablename__ = 'leave_record'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.BigInteger, db.ForeignKey('course.id', ondelete='SET NULL'))  # 可为空表示整天请假
    leave_type = db.Column(db.String(20))  # sick-病假, personal-事假
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending-待审批, approved-已批准, rejected-已拒绝
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('teacher.id', ondelete='SET NULL'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_student_date', 'student_id', 'start_date', 'end_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_code': self.student.student_code if self.student else None,
            'course_id': self.course_id,
            'course_name': self.course.course_name if self.course else None,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'reason': self.reason,
            'status': self.status,
            'teacher_id': self.teacher_id,
            'approver_name': self.approver.name if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
