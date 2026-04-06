package com.face.dto;

public class AttendanceRequest {
    private Long courseId;
    private String checkInType;
    private String imageData;

    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public String getCheckInType() { return checkInType; }
    public void setCheckInType(String checkInType) { this.checkInType = checkInType; }
    public String getImageData() { return imageData; }
    public void setImageData(String imageData) { this.imageData = imageData; }
}
