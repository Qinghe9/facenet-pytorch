package com.face.dto;

import java.math.BigDecimal;

public class FaceRecognitionResult {
    private Long studentId;
    private String studentCode;
    private String studentName;
    private BigDecimal similarity;
    private Boolean isMatch;
    private String message;

    public Long getStudentId() { return studentId; }
    public void setStudentId(Long studentId) { this.studentId = studentId; }
    public String getStudentCode() { return studentCode; }
    public void setStudentCode(String studentCode) { this.studentCode = studentCode; }
    public String getStudentName() { return studentName; }
    public void setStudentName(String studentName) { this.studentName = studentName; }
    public BigDecimal getSimilarity() { return similarity; }
    public void setSimilarity(BigDecimal similarity) { this.similarity = similarity; }
    public Boolean getIsMatch() { return isMatch; }
    public void setIsMatch(Boolean isMatch) { this.isMatch = isMatch; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}
