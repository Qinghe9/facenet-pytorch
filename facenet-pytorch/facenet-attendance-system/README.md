# 人脸识别考勤系统

基于FaceNet的人脸识别考勤系统，使用Python Flask框架和MySQL数据库。

## 功能特性

### 1. 学生信息管理
- 人脸注册：通过摄像头采集3-5张不同角度的人脸图像，提取特征值存入数据库
- 班级管理：实现班级信息的增、删、改、查功能
- 学生管理：学生信息的增、删、改、查

### 2. 考勤打卡与识别
- 实时检测：调用摄像头实时捕获画面，检测画面中的人脸位置
- 身份识别：将捕获到的人脸与数据库中已注册的人脸进行特征比对
- 考勤记录：识别成功后自动记录考勤信息

### 3. 考勤数据管理（教师端）
- 课程管理：教师可以创建课程，并关联参与该课程的学生名单
- 考勤报表：按课程、按日期、按学生维度生成考勤统计表
- 数据导出：支持将考勤记录导出为Excel格式
- 异常处理：支持教师手动修改考勤结果

### 4. 学生端/查询功能
- 考勤查询：学生可查看自己的历史考勤记录

## 技术栈

- **后端框架**: Flask 2.3.3
- **数据库**: MySQL 8.0
- **ORM**: Flask-SQLAlchemy
- **人脸识别**: PyTorch (FaceNet with MobileNet backbone)
- **图像处理**: OpenCV, Pillow, NumPy
- **前端**: HTML5, Bootstrap 5, jQuery

## 项目结构

```
facenet-attendance-system/
├── app.py                    # Flask应用入口
├── config.py                 # 配置文件
├── requirements.txt          # Python依赖
├── database.sql              # 数据库Schema
├── models/                   # 数据模型
│   ├── teacher.py
│   ├── student.py
│   ├── class_info.py
│   ├── course.py
│   ├── attendance.py
│   ├── leave.py
│   └── face.py
├── services/                 # 业务服务
│   ├── face_service.py       # 人脸识别服务
│   ├── attendance_service.py # 考勤服务
│   └── export_service.py     # 导出服务
├── routes/                   # 路由控制器
│   ├── auth.py               # 认证
│   ├── student.py            # 学生管理
│   ├── teacher.py            # 教师管理
│   ├── attendance.py         # 考勤管理
│   └── face.py               # 人脸管理
├── templates/                # HTML模板
│   ├── login.html
│   ├── teacher/
│   ├── student/
│   └── face/
├── utils/                    # 工具类
│   ├── face_detector.py
│   └── db.py
└── uploads/                  # 上传文件目录
```

## 安装部署

### 1. 环境要求

- Python 3.8+
- MySQL 8.0+
- CUDA (可选，用于GPU加速)

### 2. 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd facenet-pytorch/facenet-attendance-system
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **配置MySQL数据库**
```sql
-- 创建数据库
CREATE DATABASE face_attendance DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE face_attendance;

-- 执行database.sql创建表
SOURCE database.sql;
```

4. **修改配置文件**

编辑 `config.py` 中的数据库配置：
```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DB = 'face_attendance'
```

5. **运行应用**
```bash
python app.py
```

6. **访问系统**

打开浏览器访问: http://localhost:5000

默认管理员账号:
- 用户名: admin
- 密码: admin123

## 使用说明

### 教师端

1. 登录后进入仪表盘
2. **学生管理**: 添加学生，采集人脸
3. **班级管理**: 创建和管理班级
4. **课程管理**: 创建课程并关联班级
5. **考勤记录**: 查看和修改考勤状态
6. **考勤报表**: 导出考勤Excel报表

### 学生端

1. 使用学号登录
2. **人脸采集**: 首次使用需采集人脸
3. **考勤查询**: 查看个人考勤记录

## 人脸模型

系统使用预训练的人脸识别模型:
- 模型路径: `../logs_robust/best_model.pth`
- 主干网络: MobileNet
- 输入尺寸: 160x160x3
- 特征维度: 128

## 注意事项

1. 首次使用需确保摄像头正常工作
2. 人脸注册时需要采集3-5张不同角度的照片
3. 签到时确保光线充足，人脸清晰
4. 定期备份数据库

## License

MIT License
