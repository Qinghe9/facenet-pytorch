package com.face.service;

import com.face.entity.ClassInfo;
import com.face.mapper.ClassInfoMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ClassService {

    @Autowired
    private ClassInfoMapper classInfoMapper;

    public List<ClassInfo> findAll() {
        return classInfoMapper.findAll();
    }

    public ClassInfo findById(Long id) {
        return classInfoMapper.findById(id);
    }

    public int save(ClassInfo classInfo) {
        if (classInfo.getId() != null) {
            return classInfoMapper.update(classInfo);
        } else {
            return classInfoMapper.insert(classInfo);
        }
    }

    public int delete(Long id) {
        return classInfoMapper.deleteById(id);
    }

    public int countStudents(Long classId) {
        return classInfoMapper.countStudentsByClass(classId);
    }
}
