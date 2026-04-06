# 人脸识别考勤系统

基于 Spring Boot + MyBatis + ONNX Runtime 的人脸识别考勤系统。

## 功能特性

- **学生管理**: 增删改查学生信息，人脸数据采集
- **课程管理**: 课程创建、编辑、删除
- **人脸签到**: 摄像头实时人脸检测与识别
- **考勤管理**: 考勤记录查看、统计、导出
- **考勤报表**: 按课程/日期/学生维度的出勤率统计
- **活体检测**: 简单纹理分析防止照片欺骗

## 技术栈

- **后端**: Spring Boot 2.7, MyBatis
- **数据库**: MySQL 8.0
- **人脸识别**: ONNX Runtime, OpenCV
- **前端**: Thymeleaf, Bootstrap 5, jQuery

## 项目结构

```
face-attendance-system/
├── src/main/java/com/face/
│   ├── config/          # 配置类
│   ├── controller/      # REST API 控制器
│   ├── dto/            # 数据传输对象
│   ├── entity/         # 实体类
│   ├── mapper/         # MyBatis Mapper
│   ├── service/        # 业务逻辑
│   └── util/           # 工具类
├── src/main/resources/
│   ├── mapper/         # MyBatis XML 映射文件
│   ├── templates/      # Thymeleaf 模板
│   ├── faces/          # 人脸图片存储
│   └── application.yml # 应用配置
├── sql/
│   └── database.sql   # 数据库脚本
├── pom.xml
└── README.md
```

## 快速开始

### 1. 环境要求

- JDK 11+
- Maven 3.6+
- MySQL 8.0+
- ONNX Runtime (自动下载)
- OpenCV (通过 Maven 依赖)

### 2. 数据库初始化

```bash
mysql -u root -p < sql/database.sql
```

### 3. 配置修改

编辑 `src/main/resources/application.yml`:

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/face_attendance
    username: your_username
    password: your_password
```

### 4. ONNX 模型配置

将训练好的人脸识别 ONNX 模型放入 `src/main/resources/model/` 目录:

```
src/main/resources/model/
├── face_detection_yunet.onnx  # 人脸检测模型
└── face_recognition.onnx      # 人脸识别模型
```

如果没有模型，系统会使用简化的 Haar Cascade 进行人脸检测。

### 5. 编译运行

```bash
cd face-attendance-system
mvn clean package -DskipTests
java -jar target/face-attendance-system-1.0.0.jar
```

访问 http://localhost:8080/face

## 默认账户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

## API 接口

### 学生管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/students | 获取所有学生 |
| GET | /api/students/{id} | 获取学生详情 |
| POST | /api/students | 新增学生 |
| PUT | /api/students/{id} | 更新学生 |
| DELETE | /api/students/{id} | 删除学生 |

### 人脸注册

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/face/register | 注册单张人脸 |
| POST | /api/face/register/batch | 批量注册人脸 |

### 考勤

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/attendance/checkin | 人脸签到 |
| GET | /api/attendance/records | 查询考勤记录 |
| GET | /api/attendance/statistics | 考勤统计 |
| GET | /api/attendance/export | 导出 Excel |

## 页面路由

- `/login` - 登录页面
- `/teacher/dashboard` - 教师工作台
- `/teacher/students` - 学生管理
- `/teacher/courses` - 课程管理
- `/teacher/attendance` - 考勤管理
- `/teacher/reports` - 考勤报表
- `/student/checkin` - 学生签到
- `/face/capture` - 人脸注册

## 活体检测

系统包含简单的活体检测功能:

1. **纹理分析**: 使用拉普拉斯算子分析图像清晰度
2. **颜色分布**: 检测异常的颜色模式
3. **边缘检测**: 分析边缘特征

更高级的活体检测（如眨眼检测、张嘴动作）需要额外的人脸关键点模型支持。

## 常见问题

### 1. 摄像头无法访问

确保浏览器有摄像头权限，HTTPS 环境下才能使用摄像头。

### 2. ONNX 模型加载失败

检查模型路径是否正确，模型文件是否完整。

### 3. 人脸识别准确率低

- 确保注册时采集了多张（3-5张）不同角度的照片
- 签到时保持正对摄像头，光线充足
- 可适当调高相似度阈值

## 许可证

MIT License
