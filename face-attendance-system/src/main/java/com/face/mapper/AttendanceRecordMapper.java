package com.face.mapper;

import com.face.entity.AttendanceRecord;
import org.apache.ibatis.annotations.*;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface AttendanceRecordMapper {

    @Select("<script>" +
            "SELECT a.*, s.name as student_name, s.student_code, c.course_name " +
            "FROM attendance_record a " +
            "LEFT JOIN student s ON a.student_id = s.id " +
            "LEFT JOIN course c ON a.course_id = c.id " +
            "WHERE 1=1 " +
            "<if test='courseId != null'> AND a.course_id = #{courseId} </if>" +
            "<if test='studentId != null'> AND a.student_id = #{studentId} </if>" +
            "<if test='startDate != null'> AND DATE(a.check_in_time) &gt;= #{startDate} </if>" +
            "<if test='endDate != null'> AND DATE(a.check_in_time) &lt;= #{endDate} </if>" +
            "<if test='status != null'> AND a.status = #{status} </if>" +
            "ORDER BY a.check_in_time DESC" +
            "</script>")
    List<AttendanceRecord> findByConditions(@Param("courseId") Long courseId,
                                             @Param("studentId") Long studentId,
                                             @Param("startDate") String startDate,
                                             @Param("endDate") String endDate,
                                             @Param("status") String status);

    @Select("SELECT a.*, s.name as student_name, s.student_code, c.course_name " +
            "FROM attendance_record a " +
            "LEFT JOIN student s ON a.student_id = s.id " +
            "LEFT JOIN course c ON a.course_id = c.id " +
            "WHERE a.course_id = #{courseId} AND DATE(a.check_in_time) = DATE(#{date})")
    List<AttendanceRecord> findByCourseIdAndDate(@Param("courseId") Long courseId, @Param("date") LocalDateTime date);

    @Select("SELECT * FROM attendance_record WHERE id = #{id}")
    AttendanceRecord findById(@Param("id") Long id);

    @Select("SELECT * FROM attendance_record WHERE student_id = #{studentId} AND course_id = #{courseId} " +
            "AND DATE(check_in_time) = DATE(#{checkInTime}) LIMIT 1")
    AttendanceRecord findByStudentAndCourseAndDate(@Param("studentId") Long studentId,
                                                    @Param("courseId") Long courseId,
                                                    @Param("checkInTime") LocalDateTime checkInTime);

    @Insert("INSERT INTO attendance_record(student_id, course_id, check_in_time, check_in_type, " +
            "status, confidence, face_image_path, remarks) " +
            "VALUES(#{studentId}, #{courseId}, #{checkInTime}, #{checkInType}, " +
            "#{status}, #{confidence}, #{faceImagePath}, #{remarks})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AttendanceRecord record);

    @Update("UPDATE attendance_record SET status=#{status}, remarks=#{remarks} WHERE id=#{id}")
    int update(AttendanceRecord record);

    @Delete("DELETE FROM attendance_record WHERE id = #{id}")
    int deleteById(@Param("id") Long id);

    @Select("SELECT COUNT(*) FROM attendance_record WHERE course_id = #{courseId} AND status = #{status} " +
            "AND DATE(check_in_time) = DATE(#{date})")
    int countByStatus(@Param("courseId") Long courseId, @Param("status") String status, @Param("date") LocalDateTime date);
}
