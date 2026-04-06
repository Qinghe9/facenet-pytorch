from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.teacher import Teacher
from models.student import Student
from models.class_info import ClassInfo
from models.course import Course, CourseStudent
from models.attendance import AttendanceRecord
from models.leave import LeaveRecord
from models.face import FaceImage
