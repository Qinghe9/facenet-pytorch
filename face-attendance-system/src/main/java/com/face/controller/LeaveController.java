package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.entity.LeaveRecord;
import com.face.service.LeaveService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/leaves")
public class LeaveController {

    @Autowired
    private LeaveService leaveService;

    @GetMapping
    public ApiResponse<List<LeaveRecord>> findAll() {
        return ApiResponse.success(leaveService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<LeaveRecord> findById(@PathVariable Long id) {
        LeaveRecord record = leaveService.findById(id);
        if (record == null) {
            return ApiResponse.error("请假记录不存在");
        }
        return ApiResponse.success(record);
    }

    @GetMapping("/student/{studentId}")
    public ApiResponse<List<LeaveRecord>> findByStudentId(@PathVariable Long studentId) {
        return ApiResponse.success(leaveService.findByStudentId(studentId));
    }

    @PostMapping
    public ApiResponse<Void> save(@RequestBody LeaveRecord record) {
        int result = leaveService.save(record);
        if (result > 0) {
            return ApiResponse.success("提交成功", null);
        }
        return ApiResponse.error("提交失败");
    }

    @PutMapping("/{id}/approve")
    public ApiResponse<Void> approve(
            @PathVariable Long id,
            @RequestParam Long teacherId,
            @RequestParam String status) {
        int result = leaveService.approve(id, teacherId, status);
        if (result > 0) {
            return ApiResponse.success("审批成功", null);
        }
        return ApiResponse.error("审批失败");
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        int result = leaveService.delete(id);
        if (result > 0) {
            return ApiResponse.success("删除成功", null);
        }
        return ApiResponse.error("删除失败");
    }
}
