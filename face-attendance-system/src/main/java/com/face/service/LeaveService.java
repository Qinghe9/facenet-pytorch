package com.face.service;

import com.face.entity.LeaveRecord;
import com.face.mapper.LeaveRecordMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class LeaveService {

    @Autowired
    private LeaveRecordMapper leaveRecordMapper;

    public List<LeaveRecord> findAll() {
        return leaveRecordMapper.findAll();
    }

    public LeaveRecord findById(Long id) {
        return leaveRecordMapper.findById(id);
    }

    public List<LeaveRecord> findByStudentId(Long studentId) {
        return leaveRecordMapper.findByStudentId(studentId);
    }

    @Transactional
    public int approve(Long recordId, Long teacherId, String status) {
        LeaveRecord record = leaveRecordMapper.findById(recordId);
        if (record == null) {
            return 0;
        }
        record.setStatus(status);
        record.setTeacherId(teacherId);
        record.setApprovedAt(LocalDateTime.now());
        return leaveRecordMapper.updateStatus(record);
    }

    public int save(LeaveRecord record) {
        if (record.getId() != null) {
            return leaveRecordMapper.updateStatus(record);
        } else {
            record.setStatus("pending");
            return leaveRecordMapper.insert(record);
        }
    }

    public int delete(Long id) {
        return leaveRecordMapper.deleteById(id);
    }
}
