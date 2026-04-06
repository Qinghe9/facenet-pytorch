package com.face.mapper;

import com.face.entity.Course;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface CourseMapper {

    @Select("SELECT c.*, t.name as teacher_name, cl.class_name " +
            "FROM course c " +
            "LEFT JOIN teacher t ON c.teacher_id = t.id " +
            "LEFT JOIN class_info cl ON c.class_id = cl.id " +
            "ORDER BY c.created_at DESC")
    List<Course> findAll();

    @Select("SELECT c.*, t.name as teacher_name, cl.class_name " +
            "FROM course c " +
            "LEFT JOIN teacher t ON c.teacher_id = t.id " +
            "LEFT JOIN class_info cl ON c.class_id = cl.id " +
            "WHERE c.id = #{id}")
    Course findById(@Param("id") Long id);

    @Select("SELECT c.*, t.name as teacher_name, cl.class_name " +
            "FROM course c " +
            "LEFT JOIN teacher t ON c.teacher_id = t.id " +
            "LEFT JOIN class_info cl ON c.class_id = cl.id " +
            "WHERE c.teacher_id = #{teacherId} ORDER BY c.week_day, c.start_time")
    List<Course> findByTeacherId(@Param("teacherId") Long teacherId);

    @Select("SELECT c.*, t.name as teacher_name, cl.class_name " +
            "FROM course c " +
            "LEFT JOIN teacher t ON c.teacher_id = t.id " +
            "LEFT JOIN class_info cl ON c.class_id = cl.id " +
            "WHERE c.class_id = #{classId} ORDER BY c.week_day, c.start_time")
    List<Course> findByClassId(@Param("classId") Long classId);

    @Select("SELECT c.*, t.name as teacher_name, cl.class_name " +
            "FROM course c " +
            "LEFT JOIN teacher t ON c.teacher_id = t.id " +
            "LEFT JOIN class_info cl ON c.class_id = cl.id " +
            "WHERE c.semester = #{semester} AND c.week_day = #{weekDay} " +
            "AND c.class_id = #{classId} ORDER BY c.start_time")
    List<Course> findBySemesterAndWeekDay(@Param("semester") String semester,
                                          @Param("weekDay") Integer weekDay,
                                          @Param("classId") Long classId);

    @Insert("INSERT INTO course(course_code, course_name, teacher_id, class_id, week_day, " +
            "start_time, end_time, location, semester) " +
            "VALUES(#{courseCode}, #{courseName}, #{teacherId}, #{classId}, #{weekDay}, " +
            "#{startTime}, #{endTime}, #{location}, #{semester})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Course course);

    @Update("UPDATE course SET course_code=#{courseCode}, course_name=#{courseName}, " +
            "teacher_id=#{teacherId}, class_id=#{classId}, week_day=#{weekDay}, " +
            "start_time=#{startTime}, end_time=#{endTime}, location=#{location}, semester=#{semester} " +
            "WHERE id=#{id}")
    int update(Course course);

    @Delete("DELETE FROM course WHERE id = #{id}")
    int deleteById(@Param("id") Long id);
}
