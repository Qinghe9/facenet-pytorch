package com.face.service;

import com.face.config.FaceConfig;
import com.face.dto.AttendanceStatistics;
import com.face.entity.AttendanceRecord;
import com.face.entity.LeaveRecord;
import com.face.entity.Student;
import com.face.mapper.AttendanceRecordMapper;
import com.face.mapper.LeaveRecordMapper;
import com.face.mapper.StudentMapper;
import com.face.mapper.CourseMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AttendanceService {

    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(AttendanceService.class);

    @Autowired
    private AttendanceRecordMapper attendanceRecordMapper;

    @Autowired
    private StudentMapper studentMapper;

    @Autowired
    private CourseMapper courseMapper;

    @Autowired
    private LeaveRecordMapper leaveRecordMapper;

    @Autowired
    private FaceRecognitionService faceRecognitionService;

    @Value("${attendance.late-threshold-minutes:15}")
    private int lateThresholdMinutes;

    @Transactional
    public Map<String, Object> checkIn(Long courseId, String imageData, String checkInType) {
        Map<String, Object> result = new HashMap<>();

        try {
            Map<String, Object> recognitionResult = faceRecognitionService.recognizeAndMatch(imageData, 0.6);
            boolean recognized = (boolean) recognitionResult.getOrDefault("matched", false);

            if (!recognized) {
                result.put("success", false);
                result.put("message", recognitionResult.getOrDefault("message", "人脸识别失败"));
                return result;
            }

            Long studentId = (Long) recognitionResult.get("studentId");
            Double similarity = (Double) recognitionResult.get("similarity");

            Student student = studentMapper.findById(studentId);
            if (student == null) {
                result.put("success", false);
                result.put("message", "学生信息不存在");
                return result;
            }

            LocalDateTime now = LocalDateTime.now();

            AttendanceRecord existing = attendanceRecordMapper.findByStudentAndCourseAndDate(
                studentId, courseId, now);
            if (existing != null) {
                result.put("success", false);
                result.put("message", "今日已签到，请勿重复操作");
                result.put("record", existing);
                return result;
            }

            String status = determineAttendanceStatus(courseId, now);

            AttendanceRecord record = new AttendanceRecord();
            record.setStudentId(studentId);
            record.setCourseId(courseId);
            record.setCheckInTime(now);
            record.setCheckInType(checkInType != null ? checkInType : "camera");
            record.setStatus(status);
            record.setConfidence(BigDecimal.valueOf(similarity));

            attendanceRecordMapper.insert(record);

            result.put("success", true);
            result.put("message", "签到成功");
            result.put("status", status);
            result.put("studentName", student.getName());
            result.put("studentCode", student.getStudentCode());
            result.put("checkInTime", now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));

            log.info("Student {} checked in successfully. Status: {}", student.getStudentCode(), status);

        } catch (Exception e) {
            log.error("Check-in failed", e);
            result.put("success", false);
            result.put("message", "签到失败: " + e.getMessage());
        }

        return result;
    }

    private String determineAttendanceStatus(Long courseId, LocalDateTime checkInTime) {
        var course = courseMapper.findById(courseId);
        if (course == null || course.getStartTime() == null) {
            return "normal";
        }

        LocalTime startTime = course.getStartTime();
        LocalTime checkTime = checkInTime.toLocalTime();

        int thresholdMinutes = lateThresholdMinutes;
        if (checkTime.isAfter(startTime.plusMinutes(thresholdMinutes))) {
            return "late";
        }

        return "normal";
    }

    public List<AttendanceRecord> findByConditions(Long courseId, Long studentId,
                                                    String startDate, String endDate, String status) {
        return attendanceRecordMapper.findByConditions(courseId, studentId, startDate, endDate, status);
    }

    public AttendanceStatistics getStatistics(Long courseId, String date) {
        AttendanceStatistics stats = new AttendanceStatistics();

        LocalDateTime dateTime = LocalDate.parse(date).atStartOfDay();

        var course = courseMapper.findById(courseId);
        if (course == null || course.getClassId() == null) {
            return stats;
        }

        List<Student> students = studentMapper.findByClassId(course.getClassId());
        stats.setTotalStudents((long) students.size());

        long normal = attendanceRecordMapper.countByStatus(courseId, "normal", dateTime);
        long late = attendanceRecordMapper.countByStatus(courseId, "late", dateTime);
        long absent = stats.getTotalStudents() - normal - late;
        if (absent < 0) absent = 0;

        stats.setNormalCount(normal);
        stats.setLateCount(late);
        stats.setAbsentCount(absent);
        stats.setLeaveCount(0L);

        long checkedIn = normal + late;
        stats.setAttendanceRate(checkedIn * 100.0 / stats.getTotalStudents());

        return stats;
    }

    @Transactional
    public boolean updateRecord(Long recordId, String status, String remarks) {
        AttendanceRecord record = attendanceRecordMapper.findById(recordId);
        if (record == null) {
            return false;
        }
        record.setStatus(status);
        record.setRemarks(remarks);
        return attendanceRecordMapper.update(record) > 0;
    }

    @Transactional
    public boolean deleteRecord(Long recordId) {
        return attendanceRecordMapper.deleteById(recordId) > 0;
    }
}
