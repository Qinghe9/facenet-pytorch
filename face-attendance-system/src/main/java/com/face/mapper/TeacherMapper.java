package com.face.mapper;

import com.face.entity.Teacher;
import org.apache.ibatis.annotations.*;

@Mapper
public interface TeacherMapper {

    @Select("SELECT * FROM teacher WHERE username = #{username}")
    Teacher findByUsername(@Param("username") String username);

    @Select("SELECT * FROM teacher WHERE id = #{id}")
    Teacher findById(@Param("id") Long id);

    @Select("SELECT * FROM teacher ORDER BY created_at DESC")
    java.util.List<Teacher> findAll();

    @Insert("INSERT INTO teacher(username, password, name, phone, email) " +
            "VALUES(#{username}, #{password}, #{name}, #{phone}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Teacher teacher);

    @Update("UPDATE teacher SET name=#{name}, phone=#{phone}, email=#{email} WHERE id=#{id}")
    int update(Teacher teacher);

    @Delete("DELETE FROM teacher WHERE id = #{id}")
    int deleteById(@Param("id") Long id);
}
