package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.entity.Student;
import com.face.service.StudentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/students")
public class StudentController {

    @Autowired
    private StudentService studentService;

    @GetMapping
    public ApiResponse<List<Student>> findAll() {
        return ApiResponse.success(studentService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Student> findById(@PathVariable Long id) {
        Student student = studentService.findById(id);
        if (student == null) {
            return ApiResponse.error("学生不存在");
        }
        return ApiResponse.success(student);
    }

    @GetMapping("/code/{studentCode}")
    public ApiResponse<Student> findByStudentCode(@PathVariable String studentCode) {
        Student student = studentService.findByStudentCode(studentCode);
        if (student == null) {
            return ApiResponse.error("学生不存在");
        }
        return ApiResponse.success(student);
    }

    @GetMapping("/class/{classId}")
    public ApiResponse<List<Student>> findByClassId(@PathVariable Long classId) {
        return ApiResponse.success(studentService.findByClassId(classId));
    }

    @PostMapping
    public ApiResponse<Void> save(@RequestBody Student student) {
        int result = studentService.save(student);
        if (result > 0) {
            return ApiResponse.success("保存成功", null);
        }
        return ApiResponse.error("保存失败");
    }

    @PutMapping("/{id}")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody Student student) {
        student.setId(id);
        int result = studentService.save(student);
        if (result > 0) {
            return ApiResponse.success("更新成功", null);
        }
        return ApiResponse.error("更新失败");
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        int result = studentService.delete(id);
        if (result > 0) {
            return ApiResponse.success("删除成功", null);
        }
        return ApiResponse.error("删除失败");
    }

    @GetMapping("/count")
    public ApiResponse<Integer> count() {
        return ApiResponse.success(studentService.countAll());
    }
}
