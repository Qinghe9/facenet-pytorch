package com.face.mapper;

import com.face.entity.ClassInfo;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface ClassInfoMapper {

    @Select("SELECT c.*, t.name as teacher_name FROM class_info c " +
            "LEFT JOIN teacher t ON c.teacher_id = t.id ORDER BY c.created_at DESC")
    List<ClassInfo> findAll();

    @Select("SELECT * FROM class_info WHERE id = #{id}")
    ClassInfo findById(@Param("id") Long id);

    @Select("SELECT * FROM class_info WHERE class_name = #{className}")
    ClassInfo findByClassName(@Param("className") String className);

    @Insert("INSERT INTO class_info(class_name, grade, teacher_id) VALUES(#{className}, #{grade}, #{teacherId})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ClassInfo classInfo);

    @Update("UPDATE class_info SET class_name=#{className}, grade=#{grade}, teacher_id=#{teacherId} WHERE id=#{id}")
    int update(ClassInfo classInfo);

    @Delete("DELETE FROM class_info WHERE id = #{id}")
    int deleteById(@Param("id") Long id);

    @Select("SELECT COUNT(*) FROM student WHERE class_id = #{classId}")
    int countStudentsByClass(@Param("classId") Long classId);
}
