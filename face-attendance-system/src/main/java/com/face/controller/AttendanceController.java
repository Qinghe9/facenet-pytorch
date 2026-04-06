package com.face.controller;

import com.face.dto.ApiResponse;
import com.face.dto.AttendanceRequest;
import com.face.dto.AttendanceStatistics;
import com.face.entity.AttendanceRecord;
import com.face.service.AttendanceService;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/attendance")
public class AttendanceController {

    @Autowired
    private AttendanceService attendanceService;

    @PostMapping("/checkin")
    public ApiResponse<Map<String, Object>> checkIn(@RequestBody AttendanceRequest request) {
        Map<String, Object> result = attendanceService.checkIn(
            request.getCourseId(),
            request.getImageData(),
            request.getCheckInType()
        );
        if ((boolean) result.getOrDefault("success", false)) {
            return ApiResponse.success("签到成功", result);
        }
        return ApiResponse.error((String) result.get("message"));
    }

    @GetMapping("/records")
    public ApiResponse<List<AttendanceRecord>> findByConditions(
            @RequestParam(required = false) Long courseId,
            @RequestParam(required = false) Long studentId,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate,
            @RequestParam(required = false) String status) {
        return ApiResponse.success(
            attendanceService.findByConditions(courseId, studentId, startDate, endDate, status)
        );
    }

    @GetMapping("/statistics")
    public ApiResponse<AttendanceStatistics> getStatistics(
            @RequestParam Long courseId,
            @RequestParam String date) {
        return ApiResponse.success(attendanceService.getStatistics(courseId, date));
    }

    @PutMapping("/records/{id}")
    public ApiResponse<Void> updateRecord(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestParam(required = false) String remarks) {
        boolean success = attendanceService.updateRecord(id, status, remarks);
        if (success) {
            return ApiResponse.success("更新成功", null);
        }
        return ApiResponse.error("更新失败");
    }

    @DeleteMapping("/records/{id}")
    public ApiResponse<Void> deleteRecord(@PathVariable Long id) {
        boolean success = attendanceService.deleteRecord(id);
        if (success) {
            return ApiResponse.success("删除成功", null);
        }
        return ApiResponse.error("删除失败");
    }

    @GetMapping("/export")
    public void exportExcel(
            @RequestParam Long courseId,
            @RequestParam String startDate,
            @RequestParam String endDate,
            HttpServletResponse response) throws IOException {

        List<AttendanceRecord> records = attendanceService.findByConditions(
            courseId, null, startDate, endDate, null);

        Workbook workbook = new XSSFWorkbook();
        Sheet sheet = workbook.createSheet("考勤记录");

        CellStyle headerStyle = workbook.createCellStyle();
        headerStyle.setFillForegroundColor(IndexedColors.GREY_25_PERCENT.getIndex());
        headerStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
        Font headerFont = workbook.createFont();
        headerFont.setBold(true);
        headerStyle.setFont(headerFont);

        String[] headers = {"学号", "姓名", "课程", "签到时间", "签到方式", "状态", "置信度", "备注"};
        Row headerRow = sheet.createRow(0);
        for (int i = 0; i < headers.length; i++) {
            Cell cell = headerRow.createCell(i);
            cell.setCellValue(headers[i]);
            cell.setCellStyle(headerStyle);
        }

        int rowNum = 1;
        for (AttendanceRecord record : records) {
            Row row = sheet.createRow(rowNum++);
            row.createCell(0).setCellValue(record.getStudentCode() != null ? record.getStudentCode() : "");
            row.createCell(1).setCellValue(record.getStudentName() != null ? record.getStudentName() : "");
            row.createCell(2).setCellValue(record.getCourseName() != null ? record.getCourseName() : "");
            row.createCell(3).setCellValue(record.getCheckInTime() != null ? record.getCheckInTime().toString() : "");
            row.createCell(4).setCellValue(record.getCheckInType() != null ? record.getCheckInType() : "");
            row.createCell(5).setCellValue(record.getStatus() != null ? record.getStatus() : "");
            row.createCell(6).setCellValue(record.getConfidence() != null ? record.getConfidence().doubleValue() : 0);
            row.createCell(7).setCellValue(record.getRemarks() != null ? record.getRemarks() : "");
        }

        for (int i = 0; i < headers.length; i++) {
            sheet.autoSizeColumn(i);
        }

        String fileName = URLEncoder.encode("考勤记录_" + startDate + "_" + endDate,
            StandardCharsets.UTF_8).replace("\\+", "%20");
        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setHeader("Content-Disposition", "attachment;filename=" + fileName + ".xlsx");
        workbook.write(response.getOutputStream());
        workbook.close();
    }
}
