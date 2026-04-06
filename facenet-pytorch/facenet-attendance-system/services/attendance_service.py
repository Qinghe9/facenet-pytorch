"""
考勤服务
"""
from datetime import datetime, time
from models import db
from models.student import Student
from models.course import Course
from models.attendance import AttendanceRecord
from models.leave import LeaveRecord
from config import Config

class AttendanceService:
    """考勤服务"""

    def __init__(self, late_minutes=15):
        self.late_minutes = late_minutes

    def determine_status(self, check_in_time, course):
        """
        根据签到时间和课程安排确定考勤状态
        """
        if course is None or course.start_time is None:
            return 'normal'

        # 获取课程开始的截止时间（上课时间 + 宽限时间）
        course_start = datetime.combine(check_in_time.date(), course.start_time)
        late_deadline = course_start.replace(
            hour=course_start.hour,
            minute=course_start.minute
        )

        # 计算迟到截止时间
        from datetime import timedelta
        late_deadline = course_start + timedelta(minutes=self.late_minutes)

        if check_in_time <= course_start:
            return 'normal'
        elif check_in_time <= late_deadline:
            return 'late'
        else:
            return 'absent'

    def record_attendance(self, student_id, course_id, check_in_time=None,
                         check_in_type='camera', confidence=None,
                         face_image_path=None, remarks=None):
        """
        记录考勤
        """
        if check_in_time is None:
            check_in_time = datetime.now()

        # 获取课程信息
        course = Course.query.get(course_id)
        if course is None:
            return None, "课程不存在"

        # 检查学生是否注册了该课程
        from models.course import CourseStudent
        cs = CourseStudent.query.filter_by(course_id=course_id, student_id=student_id).first()
        if cs is None:
            return None, "学生未注册该课程"

        # 检查是否已有考勤记录
        existing = AttendanceRecord.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            check_in_time=check_in_time
        ).first()

        if existing:
            return existing, "已有考勤记录"

        # 确定考勤状态
        status = self.determine_status(check_in_time, course)

        # 检查是否有请假记录
        check_date = check_in_time.date()
        leave = LeaveRecord.query.filter(
            LeaveRecord.student_id == student_id,
            LeaveRecord.status == 'approved',
            LeaveRecord.start_date <= check_date,
            LeaveRecord.end_date >= check_date
        ).first()

        if leave:
            status = 'leave'

        # 创建考勤记录
        record = AttendanceRecord(
            student_id=student_id,
            course_id=course_id,
            check_in_time=check_in_time,
            check_in_type=check_in_type,
            status=status,
            confidence=confidence,
            face_image_path=face_image_path,
            remarks=remarks
        )

        db.session.add(record)
        db.session.commit()

        return record, "考勤记录成功"

    def get_attendance_statistics(self, course_id, start_date=None, end_date=None):
        """
        获取考勤统计
        """
        query = AttendanceRecord.query.filter_by(course_id=course_id)

        if start_date:
            query = query.filter(AttendanceRecord.check_in_time >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.check_in_time <= end_date)

        records = query.all()

        stats = {
            'total': len(records),
            'normal': 0,
            'late': 0,
            'absent': 0,
            'leave': 0
        }

        for record in records:
            if record.status in stats:
                stats[record.status] += 1

        # 计算出勤率
        if stats['total'] > 0:
            stats['attendance_rate'] = (stats['normal'] + stats['leave']) / stats['total'] * 100
        else:
            stats['attendance_rate'] = 0

        return stats

    def get_student_attendance(self, student_id, course_id=None, start_date=None, end_date=None):
        """
        获取学生的考勤记录
        """
        query = AttendanceRecord.query.filter_by(student_id=student_id)

        if course_id:
            query = query.filter_by(course_id=course_id)
        if start_date:
            query = query.filter(AttendanceRecord.check_in_time >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.check_in_time <= end_date)

        return query.order_by(AttendanceRecord.check_in_time.desc()).all()

    def update_attendance_status(self, record_id, new_status, remarks=None):
        """
        更新考勤状态（教师手动修改）
        """
        record = AttendanceRecord.query.get(record_id)
        if record is None:
            return None, "考勤记录不存在"

        record.status = new_status
        if remarks:
            record.remarks = remarks

        db.session.commit()
        return record, "更新成功"
