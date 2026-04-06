package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.entity.Course;
import com.face.service.CourseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/courses")
public class CourseController {

    @Autowired
    private CourseService courseService;

    @GetMapping
    public ApiResponse<List<Course>> findAll() {
        return ApiResponse.success(courseService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Course> findById(@PathVariable Long id) {
        Course course = courseService.findById(id);
        if (course == null) {
            return ApiResponse.error("课程不存在");
        }
        return ApiResponse.success(course);
    }

    @GetMapping("/teacher/{teacherId}")
    public ApiResponse<List<Course>> findByTeacherId(@PathVariable Long teacherId) {
        return ApiResponse.success(courseService.findByTeacherId(teacherId));
    }

    @GetMapping("/class/{classId}")
    public ApiResponse<List<Course>> findByClassId(@PathVariable Long classId) {
        return ApiResponse.success(courseService.findByClassId(classId));
    }

    @GetMapping("/today/{classId}")
    public ApiResponse<List<Course>> findTodayCourses(@PathVariable Long classId) {
        return ApiResponse.success(courseService.findTodayCourses(classId));
    }

    @PostMapping
    public ApiResponse<Void> save(@RequestBody Course course) {
        int result = courseService.save(course);
        if (result > 0) {
            return ApiResponse.success("保存成功", null);
        }
        return ApiResponse.error("保存失败");
    }

    @PutMapping("/{id}")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody Course course) {
        course.setId(id);
        int result = courseService.save(course);
        if (result > 0) {
            return ApiResponse.success("更新成功", null);
        }
        return ApiResponse.error("更新失败");
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        int result = courseService.delete(id);
        if (result > 0) {
            return ApiResponse.success("删除成功", null);
        }
        return ApiResponse.error("删除失败");
    }
}
