# 人脸识别考勤系统

基于 FaceNet 的人脸识别考勤系统，使用 Python Flask 框架和 MySQL 数据库。

## 功能特性

### 1. 学生信息管理
- **人脸注册**：通过摄像头采集3-5张不同角度的人脸图像，提取特征值存入数据库
- **班级管理**：实现班级信息的增、删、改、查功能
- **学生管理**：学生信息的增、删、改、查

### 2. 考勤打卡与识别
- **实时检测**：调用摄像头实时捕获画面，检测画面中的人脸位置
- **身份识别**：将捕获到的人脸与数据库中已注册的人脸进行特征比对
- **考勤记录**：识别成功后自动记录考勤信息（正常/迟到/缺勤/请假）

### 3. 考勤数据管理（教师端）
- **课程管理**：教师可以创建课程，并关联参与该课程的学生名单
- **考勤报表**：按课程、按日期、按学生维度生成考勤统计表
- **数据导出**：支持将考勤记录导出为 Excel 格式
- **异常处理**：支持教师手动修改考勤结果（如补签、请假审批）

### 4. 学生端/查询功能
- **考勤查询**：学生可通过学号登录，查看自己的历史考勤记录

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Bootstrap 5 + jQuery)            │
├─────────────────────────────────────────────────────────────┤
│                    Flask Web Server                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  Auth   │ │Teacher  │ │Student  │ │  Face   │          │
│  │ Routes  │ │ Routes  │ │ Routes  │ │ Routes  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
├─────────────────────────────────────────────────────────────┤
│                      业务服务层                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ FaceService     │  │ AttendanceService│  │ExportService│ │
│  │ (人脸识别)      │  │ (考勤管理)       │  │ (Excel导出) │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      数据模型层 (SQLAlchemy)                 │
│  Teacher | Student | ClassInfo | Course | Attendance | Leave│
├─────────────────────────────────────────────────────────────┤
│                      MySQL Database                         │
└─────────────────────────────────────────────────────────────┘
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask 2.3.3 |
| 数据库 | MySQL 8.0 |
| ORM | Flask-SQLAlchemy |
| 人脸识别 | PyTorch (FaceNet + MobileNet) |
| 图像处理 | OpenCV, Pillow, NumPy |
| 前端 | HTML5, Bootstrap 5.3, jQuery |
| Excel导出 | openpyxl |

## 项目结构

```
facenet-attendance-system/
├── app.py                      # Flask 应用入口
├── config.py                   # 配置文件
├── requirements.txt            # Python 依赖
├── database.sql                # 数据库 Schema
├── README.md                   # 项目文档
│
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── teacher.py              # 教师模型
│   ├── student.py              # 学生模型
│   ├── class_info.py           # 班级模型
│   ├── course.py               # 课程模型
│   ├── attendance.py           # 考勤记录模型
│   ├── leave.py                # 请假记录模型
│   └── face.py                 # 人脸图片模型
│
├── services/                   # 业务服务
│   ├── face_service.py         # 人脸识别服务
│   ├── attendance_service.py   # 考勤服务
│   └── export_service.py       # Excel 导出服务
│
├── routes/                     # 路由控制器
│   ├── auth.py                 # 认证路由
│   ├── teacher.py              # 教师端路由
│   ├── student.py              # 学生端路由
│   ├── attendance.py           # 考勤路由
│   └── face.py                 # 人脸路由
│
├── templates/                   # HTML 模板
│   ├── login.html              # 登录页面
│   ├── teacher/                # 教师端页面
│   │   ├── dashboard.html      # 仪表盘
│   │   ├── students.html       # 学生管理
│   │   ├── classes.html        # 班级管理
│   │   ├── courses.html        # 课程管理
│   │   ├── attendance.html     # 考勤记录
│   │   └── reports.html        # 考勤报表
│   ├── student/                # 学生端页面
│   │   └── query.html          # 考勤查询
│   └── face/                   # 人脸页面
│       ├── capture.html        # 人脸采集
│       └── register.html       # 人脸管理
│
└── utils/                      # 工具类
    ├── face_detector.py        # OpenCV 人脸检测
    └── db.py                   # 数据库工具
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 8.0+
- CUDA (可选，用于 GPU 加速)

### 2. 安装步骤

**步骤 1: 克隆项目**
```bash
git clone https://github.com/Qinghe9/Facial-recognition-system.git
cd Facial-recognition-system/facenet-attendance-system
```

**步骤 2: 创建 MySQL 数据库**
```sql
-- 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE face_attendance DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE face_attendance;

-- 执行 SQL 脚本创建表
SOURCE database.sql;

-- 退出
EXIT;
```

**步骤 3: 安装 Python 依赖**
```bash
pip install -r requirements.txt
```

**步骤 4: 修改配置文件**

编辑 `config.py` 中的数据库配置：
```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'  # 修改为你的密码
MYSQL_DB = 'face_attendance'
```

**步骤 5: 运行应用**
```bash
python app.py
```

**步骤 6: 访问系统**

打开浏览器访问: http://localhost:5000

### 3. 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

## 使用说明

### 教师端操作流程

1. **登录系统** → 进入教师仪表盘
2. **班级管理** → 创建班级（如：2024级计算机1班）
3. **学生管理** → 添加学生信息
4. **人脸管理** → 为学生采集人脸（3-5张不同角度）
5. **课程管理** → 创建课程并关联班级
6. **考勤报表** → 查看统计数据，导出 Excel

### 学生端操作流程

1. **学号登录** → 使用学号和密码登录
2. **人脸采集** → 首次使用需采集人脸
3. **考勤查询** → 查看个人考勤记录

## 人脸识别模型

系统使用预训练的 FaceNet 模型进行人脸识别：

| 参数 | 值 |
|------|------|
| 模型路径 | `../logs_robust/best_model.pth` |
| 主干网络 | MobileNet |
| 输入尺寸 | 160 × 160 × 3 |
| 特征维度 | 128 |
| 比对阈值 | 0.7 |

## 数据库表结构

| 表名 | 说明 |
|------|------|
| teacher | 教师表 |
| class_info | 班级表 |
| student | 学生表 |
| course | 课程表 |
| course_student | 课程-学生关联表 |
| attendance_record | 考勤记录表 |
| leave_record | 请假记录表 |
| face_image | 人脸图片表 |

## API 接口

### 认证接口
- `POST /login` - 用户登录
- `GET /logout` - 退出登录
- `GET /api/check_session` - 检查会话状态

### 学生接口
- `GET /api/students` - 获取学生列表
- `POST /api/students` - 创建学生
- `PUT /api/students/<id>` - 更新学生
- `DELETE /api/students/<id>` - 删除学生

### 人脸接口
- `POST /api/face/upload` - 上传人脸图片
- `POST /api/face/register/<student_id>` - 注册人脸特征
- `POST /api/face/recognize` - 人脸识别签到

### 考勤接口
- `GET /api/attendance` - 获取考勤记录
- `PUT /api/attendance/<id>` - 更新考勤状态
- `GET /api/attendance/statistics` - 获取考勤统计
- `GET /api/attendance/export` - 导出考勤记录

## 注意事项

1. **摄像头权限**: 首次使用需允许浏览器访问摄像头
2. **人脸采集**: 建议采集 3-5 张不同角度、光照条件下的人脸照片
3. **签到环境**: 签到时确保光线充足，人脸清晰可见
4. **数据备份**: 定期备份 MySQL 数据库
5. **密码安全**: 部署时请修改默认管理员密码

## 开发指南

### 启动开发服务器
```bash
python app.py  # 开发模式运行在 http://localhost:5000
```

### 运行测试
```bash
# 待添加
```

## License

MIT License

## 作者

Qinghe9

## 更新日志

### v1.0.0 (2024-04-06)
- 初始版本
- 实现学生信息管理
- 实现人脸注册与识别
- 实现考勤打卡功能
- 实现考勤报表导出
