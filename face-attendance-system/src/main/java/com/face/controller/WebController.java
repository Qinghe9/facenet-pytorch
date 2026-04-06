package com.face.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class WebController {

    @GetMapping("/")
    public String index() {
        return "redirect:/login";
    }

    @GetMapping("/login")
    public String login() {
        return "login";
    }

    @GetMapping("/teacher/dashboard")
    public String teacherDashboard() {
        return "teacher/dashboard";
    }

    @GetMapping("/teacher/students")
    public String teacherStudents() {
        return "teacher/students";
    }

    @GetMapping("/teacher/courses")
    public String teacherCourses() {
        return "teacher/courses";
    }

    @GetMapping("/teacher/attendance")
    public String teacherAttendance() {
        return "teacher/attendance";
    }

    @GetMapping("/teacher/reports")
    public String teacherReports() {
        return "teacher/reports";
    }

    @GetMapping("/student/checkin")
    public String studentCheckin() {
        return "student/checkin";
    }

    @GetMapping("/student/query")
    public String studentQuery() {
        return "student/query";
    }

    @GetMapping("/face/capture")
    public String faceCapture() {
        return "face/capture";
    }
}
