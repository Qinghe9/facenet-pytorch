# 人脸识别考勤系统 - 技术文档

## 一、系统概述

### 1.1 项目简介

本系统是一个基于人脸识别技术的智能考勤管理系统，采用 Spring Boot + MyBatis + ONNX Runtime 架构，实现学生人脸注册、课堂考勤自动化、考勤数据管理等功能。

### 1.2 功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端展示层                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 登录页  │ │ 教师端  │ │ 学生端  │ │人脸注册 │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────────────────┤
│                       REST API 层                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │StudentAPI│ │CourseAPI │ │AttendAPI │ │ FaceAPI  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      业务逻辑层 (Service)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Student   │ │ Course   │ │Attendance│ │  Face    │       │
│  │Service   │ │ Service  │ │ Service  │ │Recognition│      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      数据访问层 (Mapper)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Teacher  │ │  Class   │ │  Course  │ │ Student  │       │
│  │  Mapper  │ │  Mapper  │ │  Mapper  │ │  Mapper  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      第三方服务层                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │  MySQL   │ │   ONNX   │ │  OpenCV  │                    │
│  │ Database │ │  Runtime │ │          │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端框架 | Spring Boot | 2.7.18 | 核心框架 |
| ORM | MyBatis | 2.3.2 | 数据库访问 |
| 数据库 | MySQL | 8.0 | 数据存储 |
| 人脸识别 | ONNX Runtime | 1.16.3 | ONNX模型推理 |
| 图像处理 | OpenCV (Java) | 4.5.3 | 人脸检测 |
| 前端模板 | Thymeleaf | - | 模板引擎 |
| UI框架 | Bootstrap | 5.3.2 | 页面样式 |
| 图表导出 | Apache POI | 5.2.5 | Excel导出 |

---

## 二、数据库设计

### 2.1 ER图

```
┌────────────┐       ┌────────────┐       ┌────────────┐
│  teacher  │       │ class_info │       │   course   │
├────────────┤       ├────────────┤       ├────────────┤
│ id (PK)   │◄──────│ teacher_id │       │ id (PK)    │
│ username  │       │ id (PK)    │◄──────│ class_id   │
│ password  │       │ class_name │       │ teacher_id │
│ name      │       │ grade      │       │ course_name│
└────────────┘       └────────────┘       └────────────┘
       │                    ▲                    │
       │                    │                    │
       │             ┌──────┴──────┐             │
       │             │   student   │             │
       │             ├─────────────┤             │
       │             │ id (PK)    │             │
       │             │ student_code│             │
       │             │ name        │             │
       │             │ class_id(FK)│◄────────────┘
       │             │ face_feature│
       │             │ face_count  │
       │             └─────────────┘
       │                    │
       │                    ▼
       │             ┌─────────────────┐
       │             │ attendance_record│
       │             ├─────────────────┤
       │             │ id (PK)        │
       └─────────────│ student_id (FK) │
       (审批请假)     │ course_id (FK)  │
                     │ check_in_time   │
                     │ status          │
                     │ confidence      │
                     └─────────────────┘
```

### 2.2 表结构说明

#### 2.2.1 teacher (教师表)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| password | VARCHAR(255) | NOT NULL | 密码(Bcrypt加密) |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| phone | VARCHAR(20) | - | 联系电话 |
| email | VARCHAR(100) | - | 邮箱 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | ON UPDATE | 更新时间 |

#### 2.2.2 class_info (班级表)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| class_name | VARCHAR(100) | NOT NULL | 班级名称 |
| grade | VARCHAR(20) | - | 年级 |
| teacher_id | BIGINT | FK | 班主任ID |

#### 2.2.3 student (学生表)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| student_code | VARCHAR(50) | UNIQUE, NOT NULL | 学号 |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| class_id | BIGINT | FK | 班级ID |
| password | VARCHAR(255) | DEFAULT '123456' | 登录密码 |
| face_feature | MEDIUMTEXT | - | 人脸特征向量(JSON) |
| face_count | INT | DEFAULT 0 | 已注册人脸数量 |
| status | TINYINT | DEFAULT 1 | 状态: 0-禁用, 1-正常 |

#### 2.2.4 course (课程表)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| course_code | VARCHAR(50) | NOT NULL | 课程代码 |
| course_name | VARCHAR(100) | NOT NULL | 课程名称 |
| teacher_id | BIGINT | FK, NOT NULL | 授课教师 |
| class_id | BIGINT | FK | 上课班级 |
| week_day | TINYINT | - | 上课星期(1-7) |
| start_time | TIME | - | 上课时间 |
| end_time | TIME | - | 下课时间 |
| location | VARCHAR(100) | - | 上课地点 |
| semester | VARCHAR(20) | - | 学期(例: 2024-1) |

#### 2.2.5 attendance_record (考勤记录表)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| student_id | BIGINT | FK, NOT NULL | 学生ID |
| course_id | BIGINT | FK, NOT NULL | 课程ID |
| check_in_time | TIMESTAMP | NOT NULL | 签到时间 |
| check_in_type | VARCHAR(20) | DEFAULT 'camera' | 签到方式 |
| status | VARCHAR(20) | NOT NULL | 考勤状态 |
| confidence | DECIMAL(5,4) | - | 识别置信度 |
| face_image_path | VARCHAR(255) | - | 人脸截图路径 |
| remarks | VARCHAR(255) | - | 备注 |

**考勤状态枚举值:**
- `normal`: 正常
- `late`: 迟到
- `absent`: 缺勤
- `leave`: 请假

#### 2.2.6 leave_record (请假记录表)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| student_id | BIGINT | FK, NOT NULL | 学生ID |
| course_id | BIGINT | FK | 课程ID(可空) |
| leave_type | VARCHAR(20) | - | 请假类型 |
| start_date | DATE | NOT NULL | 请假开始日期 |
| end_date | DATE | NOT NULL | 请假结束日期 |
| reason | TEXT | - | 请假原因 |
| status | VARCHAR(20) | DEFAULT 'pending' | 审批状态 |

---

## 三、核心模块设计

### 3.1 人脸识别模块 (FaceRecognitionService)

#### 3.1.1 整体流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  输入图片   │───►│ 人脸检测    │───►│ 特征提取    │───►│ 特征比对    │
│(Base64/文件)│    │ (OpenCV)   │    │  (ONNX)    │    │ (余弦相似度)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │ 返回匹配结果 │
                                                            └─────────────┘
```

#### 3.1.2 核心算法

**特征提取 (ONNX推理):**
```java
// 输入: 160x160x3 RGB图像
// 输出: 512维特征向量
float[] extractFeature(Mat image) {
    // 1. 人脸检测与对齐
    Rect faceRect = detectFace(image);

    // 2. 人脸区域裁剪与resize
    Mat face = cropAndResize(image, faceRect, 160);

    // 3. 图像归一化 [0,1]
    Mat normalized = face / 255.0;

    // 4. ONNX推理
    float[] features = onnxInference(normalized);

    // 5. L2归一化
    return normalize(features);
}
```

**特征比对 (余弦相似度):**
```java
float cosineSimilarity(float[] a, float[] b) {
    float dot = 0;
    for (int i = 0; i < a.length; i++) {
        dot += a[i] * b[i];
    }
    return dot;  // 已归一化向量，相乘即余弦相似度
}
```

#### 3.1.3 人脸注册流程

```
┌─────────────┐
│ 采集3-5张   │  用户拍摄多角度照片
│ 不同角度照片 │
└─────────────┘
       │
       ▼
┌─────────────┐
│  人脸检测   │  OpenCV检测每张图片中的人脸
└─────────────┘
       │
       ▼
┌─────────────┐
│  特征提取   │  ONNX模型提取512维特征
└─────────────┘
       │
       ▼
┌─────────────┐
│  特征融合   │  多张特征求均值再归一化
└─────────────┘
       │
       ▼
┌─────────────┐
│  存储数据库 │  JSON格式存储到student表
└─────────────┘
```

### 3.2 考勤模块 (AttendanceService)

#### 3.2.1 签到流程

```
┌─────────────┐
│ 选择课程    │  学生从今日课程中选择
└─────────────┘
       │
       ▼
┌─────────────┐
│  拍照采集   │  通过摄像头捕获人脸图片
└─────────────┘
       │
       ▼
┌─────────────┐
│ 活体检测    │  纹理分析确认真实人脸(可选)
└─────────────┘
       │
       ▼
┌─────────────┐
│ 人脸识别    │  与数据库特征比对
└─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ 相似度>阈值  │────►│  签到成功   │
│ (默认0.6)   │     │ 记录状态    │
└─────────────┘     └─────────────┘
       │
       │ 相似度<阈值
       ▼
┌─────────────┐
│  签到失败   │
└─────────────┘
```

#### 3.2.2 考勤状态判定

```java
String determineAttendanceStatus(Long courseId, LocalDateTime checkInTime) {
    Course course = courseMapper.findById(courseId);

    // 获取课程开始时间
    LocalTime startTime = course.getStartTime();
    LocalTime checkTime = checkInTime.toLocalTime();

    // 超过15分钟视为迟到
    if (checkTime.isAfter(startTime.plusMinutes(15))) {
        return "late";
    }
    return "normal";
}
```

### 3.3 活体检测模块 (LivenessDetectionService)

#### 3.3.1 检测方法

**1. 纹理分析 (Laplacian Variance)**
- 原理: 真实人脸有丰富的纹理细节
- 方法: 计算Laplacian算子的方差
- 阈值: 方差在合理范围(20-100)视为正常

**2. 颜色分布分析**
- 原理: 屏幕翻拍会有异常的颜色模式(摩尔纹)
- 方法: 分析RGB三通道的统计分布
- 判定: 通道方差异常时可能是翻拍

**3. 边缘检测 (Canny)**
- 原理: 照片边缘可能有反射或阴影
- 方法: Canny边缘检测计算边缘密度
- 阈值: 密度在0.05-0.4之间正常

#### 3.3.2 综合评分

```java
double finalScore =
    textureScore * 0.4 +   // 纹理权重40%
    colorScore * 0.3 +     // 颜色权重30%
    edgeScore * 0.3;       // 边缘权重30%

// finalScore > 0.6 认为是活体
```

---

## 四、API接口设计

### 4.1 学生管理 API

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| GET | `/api/students` | 获取所有学生 | - |
| GET | `/api/students/{id}` | 获取学生详情 | - |
| GET | `/api/students/code/{code}` | 按学号查询 | - |
| GET | `/api/students/class/{classId}` | 按班级查询 | - |
| POST | `/api/students` | 新增学生 | Student |
| PUT | `/api/students/{id}` | 更新学生 | Student |
| DELETE | `/api/students/{id}` | 删除学生 | - |
| GET | `/api/students/count` | 统计学生数 | - |

**Student 请求体示例:**
```json
{
    "studentCode": "2024001",
    "name": "张三",
    "classId": 1,
    "password": "123456",
    "phone": "13800138000",
    "email": "zhangsan@school.edu"
}
```

### 4.2 人脸注册 API

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| POST | `/api/face/register` | 注册单张人脸 | FaceRegisterRequest |
| POST | `/api/face/register/batch` | 批量注册 | List<FaceRegisterRequest> |

**FaceRegisterRequest 请求体:**
```json
{
    "studentId": 1,
    "imageData": "base64编码的图片数据"
}
```

**响应示例:**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "faceCount": 3
    }
}
```

### 4.3 考勤 API

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| POST | `/api/attendance/checkin` | 人脸签到 | AttendanceRequest |
| GET | `/api/attendance/records` | 查询考勤记录 | courseId, studentId, startDate, endDate, status |
| GET | `/api/attendance/statistics` | 考勤统计 | courseId, date |
| PUT | `/api/attendance/records/{id}` | 修改记录 | status, remarks |
| DELETE | `/api/attendance/records/{id}` | 删除记录 | - |
| GET | `/api/attendance/export` | 导出Excel | courseId, startDate, endDate |

**AttendanceRequest 请求体:**
```json
{
    "courseId": 1,
    "imageData": "base64编码的图片数据",
    "checkInType": "camera"
}
```

**签到响应示例:**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "success": true,
        "studentName": "张三",
        "studentCode": "2024001",
        "status": "normal",
        "checkInTime": "2024-04-04 08:30:00"
    }
}
```

---

## 五、前端页面结构

### 5.1 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | login | 重定向到登录页 |
| `/login` | login.html | 登录页 |
| `/teacher/dashboard` | teacher/dashboard.html | 教师工作台 |
| `/teacher/students` | teacher/students.html | 学生管理 |
| `/teacher/courses` | teacher/courses.html | 课程管理 |
| `/teacher/attendance` | teacher/attendance.html | 考勤管理 |
| `/teacher/reports` | teacher/reports.html | 考勤报表 |
| `/student/checkin` | student/checkin.html | 学生签到 |
| `/student/query` | student/query.html | 考勤查询 |
| `/face/capture` | face/capture.html | 人脸注册 |

### 5.2 教师端页面布局

```
┌──────────┬──────────────────────────────────────────┐
│          │  顶部导航栏                               │
│  侧边栏   │  ──────────────────────────────────────── │
│          │                                          │
│  ◉ 工作台 │        主内容区域                         │
│  ◉ 学生   │                                          │
│  ◉ 课程   │                                          │
│  ◉ 考勤   │                                          │
│  ◉ 报表   │                                          │
│  ◉ 人脸   │                                          │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

### 5.3 核心交互流程

**学生签到页面流程:**
```
┌─────────────────────────────────────────┐
│           选择课程 (下拉框)              │
├─────────────────────────────────────────┤
│                                         │
│         [摄像头实时预览画面]              │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│        [ 拍照签到 ] 按钮                │
└─────────────────────────────────────────┘
         │
         ▼ 点击按钮
┌─────────────────────────────────────────┐
│  canvas截取视频帧 → 转Base64 → API调用  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  识别成功: 显示学生信息 + 成功提示        │
│  识别失败: 显示错误信息                  │
└─────────────────────────────────────────┘
```

---

## 六、配置文件说明

### 6.1 application.yml

```yaml
server:
  port: 8080              # 服务端口
  servlet:
    context-path: /face   # 应用上下文路径

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/face_attendance
    username: root
    password: root
  thymeleaf:
    prefix: classpath:/templates/
    suffix: .html

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.face.entity

face:
  model:
    detmodel-path: src/main/resources/model/face_detection_yunet.onnx
    recmodel-path: src/main/resources/model/face_recognition.onnx
    embedding-size: 512        # 特征向量维度
    similarity-threshold: 0.6 # 相似度阈值
    min-face-size: 40         # 最小人脸尺寸
    input-size: 160           # 模型输入尺寸

attendance:
  late-threshold-minutes: 15  # 迟到判定阈值(分钟)
```

### 6.2 pom.xml 关键依赖

```xml
<!-- Spring Boot -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.18</version>
</parent>

<!-- ONNX Runtime -->
<dependency>
    <groupId>com.microsoft.onnxruntime</groupId>
    <artifactId>onnxruntime</artifactId>
    <version>1.16.3</version>
</dependency>

<!-- OpenCV -->
<dependency>
    <groupId>org.openpnp</groupId>
    <artifactId>opencv</artifactId>
    <version>4.5.3-0</version>
</dependency>

<!-- MyBatis -->
<dependency>
    <groupId>org.mybatis.spring.boot</groupId>
    <artifactId>mybatis-spring-boot-starter</artifactId>
    <version>2.3.2</version>
</dependency>
```

---

## 七、部署指南

### 7.1 环境要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| JDK | 11+ | 推荐JDK 17 |
| Maven | 3.6+ | 构建工具 |
| MySQL | 8.0+ | 数据库 |
| 内存 | 4GB+ | 推荐8GB |
| 磁盘 | 10GB+ | 模型文件较大 |

### 7.2 部署步骤

**1. 数据库初始化**
```bash
mysql -u root -p < sql/database.sql
```

**2. 修改数据库配置**
编辑 `src/main/resources/application.yml`:
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/face_attendance
    username: your_username
    password: your_password
```

**3. 放置ONNX模型文件**
```
src/main/resources/model/
├── face_detection_yunet.onnx  # 人脸检测模型(可选)
└── face_recognition.onnx     # 人脸识别模型(必须)
```

**4. 编译打包**
```bash
mvn clean package -DskipTests
```

**5. 运行**
```bash
java -jar target/face-attendance-system-1.0.0.jar
```

**6. 访问**
- 网址: http://localhost:8080/face
- 默认账户: admin / admin123

### 7.3 摄像头访问说明

浏览器调用摄像头需要:
1. 使用HTTPS访问(生产环境)
2. 或在本地localhost访问(开发环境)
3. 用户授权摄像头权限

---

## 八、性能优化建议

### 8.1 人脸识别性能

| 优化项 | 建议 | 效果 |
|--------|------|------|
| 特征缓存 | Redis缓存已提取的特征 | 减少重复计算 |
| 并行比对 | 多线程批量比对 | 提升大库查询速度 |
| 模型量化 | FP16/INT8量化 | 推理速度提升2-4倍 |
| 人脸检测优化 | 使用GPU版本的OpenCV | 检测速度提升5倍 |

### 8.2 数据库优化

| 优化项 | 说明 |
|--------|------|
| 索引优化 | student_code, course_id, check_in_time建索引 |
| 分表 | 按学期分表存储考勤记录 |
| 连接池 | 使用HikariCP连接池 |

### 8.3 前端优化

| 优化项 | 说明 |
|--------|------|
| 视频帧率 | 限制预览帧率15fps减少资源占用 |
| 人脸检测 | 前端JS先做粗检测，减少无效请求 |
| 图片压缩 | Base64前适当压缩图片尺寸 |

---

## 九、常见问题排查

### 9.1 摄像头无法访问
```
错误: Navigator.mediaDevices.getUserMedia failed
解决:
1. 检查浏览器是否支持getUserMedia API
2. 确认用户已授权摄像头权限
3. HTTPS环境下才能使用摄像头(localhost除外)
```

### 9.2 ONNX模型加载失败
```
错误: ONNX model load failed
解决:
1. 检查模型文件路径是否正确
2. 确认模型文件完整性(非空文件)
3. 确认ONNX Runtime版本兼容
```

### 9.3 人脸识别准确率低
```
可能原因:
1. 注册时人脸样本不足(建议3-5张)
2. 光线条件差
3. 面部有遮挡(眼镜、口罩)
4. 摄像头分辨率低

解决:
1. 重新注册高质量人脸样本
2. 调低相似度阈值(但会增加误识别风险)
3. 改善光线条件
```

### 9.4 数据库连接失败
```
错误: Connection refused
解决:
1. 检查MySQL服务是否启动
2. 确认端口3306未被占用
3. 检查用户名密码是否正确
4. 确认数据库已创建
```

---

## 十、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2024-04-04 | 初始版本，完成基础功能 |

---

## 附录A: 数据库初始化SQL

详见 `sql/database.sql` 文件。

## 附录B: API响应格式

```java
public class ApiResponse<T> {
    Integer code;    // 状态码: 200成功, 500失败
    String message;  // 消息
    T data;         // 数据
}
```
