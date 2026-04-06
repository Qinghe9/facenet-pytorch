package com.face.service;

import com.face.entity.Course;
import com.face.mapper.CourseMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CourseService {

    @Autowired
    private CourseMapper courseMapper;

    public List<Course> findAll() {
        return courseMapper.findAll();
    }

    public Course findById(Long id) {
        return courseMapper.findById(id);
    }

    public List<Course> findByTeacherId(Long teacherId) {
        return courseMapper.findByTeacherId(teacherId);
    }

    public List<Course> findByClassId(Long classId) {
        return courseMapper.findByClassId(classId);
    }

    public List<Course> findTodayCourses(Long classId) {
        int dayOfWeek = java.time.LocalDate.now().getDayOfWeek().getValue();
        String semester = getCurrentSemester();
        return courseMapper.findBySemesterAndWeekDay(semester, dayOfWeek, classId);
    }

    private String getCurrentSemester() {
        java.time.LocalDate now = java.time.LocalDate.now();
        int year = now.getYear();
        int month = now.getMonthValue();
        if (month >= 9 || month <= 1) {
            return year + "-1";
        } else if (month >= 2 && month <= 7) {
            return (year - 1) + "-2";
        }
        return year + "-1";
    }

    public int save(Course course) {
        if (course.getId() != null) {
            return courseMapper.update(course);
        } else {
            return courseMapper.insert(course);
        }
    }

    public int delete(Long id) {
        return courseMapper.deleteById(id);
    }
}
