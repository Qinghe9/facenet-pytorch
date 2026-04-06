package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.entity.ClassInfo;
import com.face.service.ClassService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/classes")
public class ClassController {

    @Autowired
    private ClassService classService;

    @GetMapping
    public ApiResponse<List<ClassInfo>> findAll() {
        return ApiResponse.success(classService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<ClassInfo> findById(@PathVariable Long id) {
        ClassInfo classInfo = classService.findById(id);
        if (classInfo == null) {
            return ApiResponse.error("班级不存在");
        }
        return ApiResponse.success(classInfo);
    }

    @PostMapping
    public ApiResponse<Void> save(@RequestBody ClassInfo classInfo) {
        int result = classService.save(classInfo);
        if (result > 0) {
            return ApiResponse.success("保存成功", null);
        }
        return ApiResponse.error("保存失败");
    }

    @PutMapping("/{id}")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody ClassInfo classInfo) {
        classInfo.setId(id);
        int result = classService.save(classInfo);
        if (result > 0) {
            return ApiResponse.success("更新成功", null);
        }
        return ApiResponse.error("更新失败");
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        int result = classService.delete(id);
        if (result > 0) {
            return ApiResponse.success("删除成功", null);
        }
        return ApiResponse.error("删除失败");
    }

    @GetMapping("/{id}/student-count")
    public ApiResponse<Integer> countStudents(@PathVariable Long id) {
        return ApiResponse.success(classService.countStudents(id));
    }
}
