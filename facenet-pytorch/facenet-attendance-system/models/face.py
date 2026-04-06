from models import db
from datetime import datetime

class FaceImage(db.Model):
    __tablename__ = 'face_image'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    feature = db.Column(db.Text)  # JSON格式存储人脸特征向量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_student_id', 'student_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
