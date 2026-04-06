package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.entity.Teacher;
import com.face.service.TeacherService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/teachers")
public class TeacherController {

    @Autowired
    private TeacherService teacherService;

    @GetMapping
    public ApiResponse<List<Teacher>> findAll() {
        return ApiResponse.success(teacherService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Teacher> findById(@PathVariable Long id) {
        Teacher teacher = teacherService.findById(id);
        if (teacher == null) {
            return ApiResponse.error("教师不存在");
        }
        return ApiResponse.success(teacher);
    }

    @GetMapping("/username/{username}")
    public ApiResponse<Teacher> findByUsername(@PathVariable String username) {
        Teacher teacher = teacherService.findByUsername(username);
        if (teacher == null) {
            return ApiResponse.error("教师不存在");
        }
        return ApiResponse.success(teacher);
    }

    @PostMapping
    public ApiResponse<Void> save(@RequestBody Teacher teacher) {
        int result = teacherService.save(teacher);
        if (result > 0) {
            return ApiResponse.success("保存成功", null);
        }
        return ApiResponse.error("保存失败");
    }

    @PutMapping("/{id}")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody Teacher teacher) {
        teacher.setId(id);
        int result = teacherService.save(teacher);
        if (result > 0) {
            return ApiResponse.success("更新成功", null);
        }
        return ApiResponse.error("更新失败");
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        int result = teacherService.delete(id);
        if (result > 0) {
            return ApiResponse.success("删除成功", null);
        }
        return ApiResponse.error("删除失败");
    }
}
