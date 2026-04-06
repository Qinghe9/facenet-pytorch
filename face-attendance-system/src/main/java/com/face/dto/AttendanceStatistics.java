package com.face.dto;

public class AttendanceStatistics {
    private Long totalStudents;
    private Long normalCount;
    private Long lateCount;
    private Long absentCount;
    private Long leaveCount;
    private Double attendanceRate;

    public Long getTotalStudents() { return totalStudents; }
    public void setTotalStudents(Long totalStudents) { this.totalStudents = totalStudents; }
    public Long getNormalCount() { return normalCount; }
    public void setNormalCount(Long normalCount) { this.normalCount = normalCount; }
    public Long getLateCount() { return lateCount; }
    public void setLateCount(Long lateCount) { this.lateCount = lateCount; }
    public Long getAbsentCount() { return absentCount; }
    public void setAbsentCount(Long absentCount) { this.absentCount = absentCount; }
    public Long getLeaveCount() { return leaveCount; }
    public void setLeaveCount(Long leaveCount) { this.leaveCount = leaveCount; }
    public Double getAttendanceRate() { return attendanceRate; }
    public void setAttendanceRate(Double attendanceRate) { this.attendanceRate = attendanceRate; }
}
