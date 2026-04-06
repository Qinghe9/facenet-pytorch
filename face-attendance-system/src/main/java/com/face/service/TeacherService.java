package com.face.service;

import com.face.entity.Teacher;
import com.face.mapper.TeacherMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TeacherService {

    @Autowired
    private TeacherMapper teacherMapper;

    public Teacher findByUsername(String username) {
        return teacherMapper.findByUsername(username);
    }

    public Teacher findById(Long id) {
        return teacherMapper.findById(id);
    }

    public List<Teacher> findAll() {
        return teacherMapper.findAll();
    }

    public int save(Teacher teacher) {
        if (teacher.getId() != null) {
            return teacherMapper.update(teacher);
        } else {
            return teacherMapper.insert(teacher);
        }
    }

    public int delete(Long id) {
        return teacherMapper.deleteById(id);
    }
}
