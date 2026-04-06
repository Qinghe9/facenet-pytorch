package com.face.mapper;

import com.face.entity.LeaveRecord;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface LeaveRecordMapper {

    @Select("SELECT l.*, s.name as student_name, s.student_code, c.course_name, t.name as teacher_name " +
            "FROM leave_record l " +
            "LEFT JOIN student s ON l.student_id = s.id " +
            "LEFT JOIN course c ON l.course_id = c.id " +
            "LEFT JOIN teacher t ON l.teacher_id = t.id " +
            "ORDER BY l.created_at DESC")
    List<LeaveRecord> findAll();

    @Select("SELECT * FROM leave_record WHERE id = #{id}")
    LeaveRecord findById(@Param("id") Long id);

    @Select("SELECT l.*, s.name as student_name, s.student_code " +
            "FROM leave_record l " +
            "LEFT JOIN student s ON l.student_id = s.id " +
            "WHERE l.student_id = #{studentId} ORDER BY l.created_at DESC")
    List<LeaveRecord> findByStudentId(@Param("studentId") Long studentId);

    @Select("SELECT * FROM leave_record WHERE student_id = #{studentId} AND status = 'approved' " +
            "AND #{date} BETWEEN start_date AND end_date LIMIT 1")
    LeaveRecord findApprovedLeave(@Param("studentId") Long studentId, @Param("date") String date);

    @Insert("INSERT INTO leave_record(student_id, course_id, leave_type, start_date, end_date, reason, status) " +
            "VALUES(#{studentId}, #{courseId}, #{leaveType}, #{startDate}, #{endDate}, #{reason}, #{status})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(LeaveRecord record);

    @Update("UPDATE leave_record SET status=#{status}, teacher_id=#{teacherId}, approved_at=#{approvedAt} WHERE id=#{id}")
    int updateStatus(LeaveRecord record);

    @Delete("DELETE FROM leave_record WHERE id = #{id}")
    int deleteById(@Param("id") Long id);
}
