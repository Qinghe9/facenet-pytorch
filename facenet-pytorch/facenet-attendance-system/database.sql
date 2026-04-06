-- 人脸识别考勤系统数据库
-- 创建数据库
CREATE DATABASE IF NOT EXISTS face_attendance DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE face_attendance;

-- 1. 教师表
CREATE TABLE IF NOT EXISTS teacher (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(加密存储)',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师表';

-- 2. 班级表
CREATE TABLE IF NOT EXISTS class_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    grade VARCHAR(20) COMMENT '年级',
    teacher_id BIGINT COMMENT '班主任ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE SET NULL,
    INDEX idx_class_name (class_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级表';

-- 3. 学生表
CREATE TABLE IF NOT EXISTS student (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    student_code VARCHAR(50) NOT NULL UNIQUE COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    class_id BIGINT COMMENT '班级ID',
    password VARCHAR(255) DEFAULT '123456' COMMENT '登录密码',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    face_feature MEDIUMTEXT COMMENT '人脸特征向量(JSON格式)',
    face_count INT DEFAULT 0 COMMENT '注册人脸数量',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用, 1-正常',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (class_id) REFERENCES class_info(id) ON DELETE SET NULL,
    INDEX idx_student_code (student_code),
    INDEX idx_class_id (class_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生表';

-- 4. 课程表
CREATE TABLE IF NOT EXISTS course (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    course_code VARCHAR(50) NOT NULL COMMENT '课程代码',
    course_name VARCHAR(100) NOT NULL COMMENT '课程名称',
    teacher_id BIGINT NOT NULL COMMENT '授课教师ID',
    class_id BIGINT COMMENT '上课班级',
    week_day TINYINT COMMENT '上课星期(1-7)',
    start_time TIME COMMENT '上课时间',
    end_time TIME COMMENT '下课时间',
    location VARCHAR(100) COMMENT '上课地点',
    semester VARCHAR(20) COMMENT '学期, 如: 2024-1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES class_info(id) ON DELETE SET NULL,
    INDEX idx_course_code (course_code),
    INDEX idx_teacher_id (teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- 5. 课程学生关联表
CREATE TABLE IF NOT EXISTS course_student (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    course_id BIGINT NOT NULL COMMENT '课程ID',
    student_id BIGINT NOT NULL COMMENT '学生ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    UNIQUE KEY uk_course_student (course_id, student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程学生关联表';

-- 6. 考勤记录表
CREATE TABLE IF NOT EXISTS attendance_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    student_id BIGINT NOT NULL COMMENT '学生ID',
    course_id BIGINT NOT NULL COMMENT '课程ID',
    check_in_time TIMESTAMP NOT NULL COMMENT '签到时间',
    check_in_type VARCHAR(20) DEFAULT 'camera' COMMENT '签到方式: camera-摄像头, manual-手动',
    status VARCHAR(20) NOT NULL COMMENT '考勤状态: normal-正常, late-迟到, absent-缺勤, leave-请假',
    confidence DECIMAL(5,4) COMMENT '识别置信度',
    face_image_path VARCHAR(255) COMMENT '签到时人脸截图路径',
    remarks VARCHAR(255) COMMENT '备注(如迟到原因)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    INDEX idx_student_course (student_id, course_id),
    INDEX idx_check_in_time (check_in_time),
    INDEX idx_course_date (course_id, check_in_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考勤记录表';

-- 7. 请假记录表
CREATE TABLE IF NOT EXISTS leave_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    student_id BIGINT NOT NULL COMMENT '学生ID',
    course_id BIGINT COMMENT '课程ID(可为空表示整天请假)',
    leave_type VARCHAR(20) COMMENT '请假类型: sick-病假, personal-事假',
    start_date DATE NOT NULL COMMENT '请假开始日期',
    end_date DATE NOT NULL COMMENT '请假结束日期',
    reason TEXT COMMENT '请假原因',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '审批状态: pending-待审批, approved-已批准, rejected-已拒绝',
    teacher_id BIGINT COMMENT '审批教师',
    approved_at TIMESTAMP NULL COMMENT '审批时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE SET NULL,
    INDEX idx_student_date (student_id, start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='请假记录表';

-- 8. 人脸图片表
CREATE TABLE IF NOT EXISTS face_image (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    student_id BIGINT NOT NULL COMMENT '学生ID',
    image_path VARCHAR(255) NOT NULL COMMENT '人脸图片路径',
    feature TEXT COMMENT '人脸特征向量(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人脸图片表';

-- 插入默认管理员账户 (密码: admin123)
INSERT INTO teacher (username, password, name, phone, email)
VALUES ('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EH', '系统管理员', '13800138000', 'admin@school.edu')
ON DUPLICATE KEY UPDATE name = name;
