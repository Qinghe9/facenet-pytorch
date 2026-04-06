package com.face.mapper;

import com.face.entity.Student;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface StudentMapper {

    @Select("SELECT s.*, c.class_name FROM student s " +
            "LEFT JOIN class_info c ON s.class_id = c.id ORDER BY s.created_at DESC")
    List<Student> findAll();

    @Select("SELECT * FROM student WHERE id = #{id}")
    Student findById(@Param("id") Long id);

    @Select("SELECT * FROM student WHERE student_code = #{studentCode}")
    Student findByStudentCode(@Param("studentCode") String studentCode);

    @Select("SELECT * FROM student WHERE class_id = #{classId} ORDER BY student_code")
    List<Student> findByClassId(@Param("classId") Long classId);

    @Select("SELECT s.*, c.class_name FROM student s " +
            "LEFT JOIN class_info c ON s.class_id = c.id " +
            "WHERE s.face_feature IS NOT NULL AND s.face_count > 0")
    List<Student> findAllWithFaceFeature();

    @Insert("INSERT INTO student(student_code, name, class_id, password, phone, email) " +
            "VALUES(#{studentCode}, #{name}, #{classId}, #{password}, #{phone}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Student student);

    @Update("UPDATE student SET name=#{name}, class_id=#{classId}, password=#{password}, " +
            "phone=#{phone}, email=#{email}, face_feature=#{faceFeature}, face_count=#{faceCount}, status=#{status} " +
            "WHERE id=#{id}")
    int update(Student student);

    @Update("UPDATE student SET face_feature=#{faceFeature}, face_count=#{faceCount} WHERE id=#{id}")
    int updateFaceFeature(@Param("id") Long id, @Param("faceFeature") String faceFeature, @Param("faceCount") Integer faceCount);

    @Delete("DELETE FROM student WHERE id = #{id}")
    int deleteById(@Param("id") Long id);

    @Select("SELECT COUNT(*) FROM student")
    int countAll();
}
