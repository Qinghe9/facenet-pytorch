package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.dto.FaceRegisterRequest;
import com.face.entity.Student;
import com.face.service.StudentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/face")
public class FaceController {

    @Autowired
    private StudentService studentService;

    @PostMapping("/register")
    public ApiResponse<Map<String, Object>> registerFace(@RequestBody FaceRegisterRequest request) {
        boolean success = studentService.registerFace(request.getStudentId(), request.getImageData());

        Map<String, Object> result = new java.util.HashMap<>();
        if (success) {
            Student student = studentService.findById(request.getStudentId());
            result.put("faceCount", student != null ? student.getFaceCount() : 1);
            return ApiResponse.success("人脸注册成功", result);
        }
        return ApiResponse.error("人脸注册失败，请确保图片中包含清晰的人脸");
    }

    @PostMapping("/register/batch")
    public ApiResponse<Map<String, Object>> registerBatchFace(@RequestBody java.util.List<FaceRegisterRequest> requests) {
        int successCount = 0;
        for (FaceRegisterRequest request : requests) {
            if (studentService.registerFace(request.getStudentId(), request.getImageData())) {
                successCount++;
            }
        }

        Map<String, Object> result = new java.util.HashMap<>();
        result.put("total", requests.size());
        result.put("success", successCount);
        result.put("failed", requests.size() - successCount);

        return ApiResponse.success("批量注册完成", result);
    }
}
