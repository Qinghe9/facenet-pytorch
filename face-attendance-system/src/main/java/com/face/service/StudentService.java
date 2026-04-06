package com.face.service;

import com.face.entity.Student;
import com.face.mapper.StudentMapper;
import com.google.gson.Gson;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class StudentService {

    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(StudentService.class);

    @Autowired
    private StudentMapper studentMapper;

    @Autowired
    private FaceRecognitionService faceRecognitionService;

    private final Gson gson = new Gson();

    public List<Student> findAll() {
        return studentMapper.findAll();
    }

    public Student findById(Long id) {
        return studentMapper.findById(id);
    }

    public Student findByStudentCode(String studentCode) {
        return studentMapper.findByStudentCode(studentCode);
    }

    public List<Student> findByClassId(Long classId) {
        return studentMapper.findByClassId(classId);
    }

    public boolean registerFace(Long studentId, String imageData) {
        try {
            Student student = studentMapper.findById(studentId);
            if (student == null) {
                log.error("Student not found: {}", studentId);
                return false;
            }

            String studentCode = student.getStudentCode();
            int currentCount = student.getFaceCount() != null ? student.getFaceCount() : 0;
            int newIndex = currentCount + 1;

            String imagePath = "src/main/resources/faces/" + studentCode + "/face_" + newIndex + ".jpg";
            new java.io.File("src/main/resources/faces/" + studentCode + "/").mkdirs();

            byte[] imageBytes = java.util.Base64.getDecoder().decode(imageData);
            org.bytedeco.opencv.opencv_core.Mat mat = org.bytedeco.opencv.global.opencv_imgcodecs.imdecode(
                new org.bytedeco.opencv.opencv_core.Mat(imageBytes), org.bytedeco.opencv.global.opencv_imgcodecs.IMREAD_UNCHANGED);
            org.bytedeco.opencv.global.opencv_imgcodecs.imwrite(imagePath, mat);

            float[] feature = faceRecognitionService.extractFeature(imagePath);
            if (feature == null) {
                log.error("Failed to extract face feature");
                return false;
            }

            String featureJson = gson.toJson(feature);

            String existingFeatures = student.getFaceFeature();
            float[] aggregatedFeature;

            if (existingFeatures != null && !existingFeatures.isEmpty()) {
                float[][] existing = gson.fromJson(existingFeatures, float[][].class);
                float[][] all = new float[existing.length + 1][];
                System.arraycopy(existing, 0, all, 0, existing.length);
                all[existing.length] = feature;
                aggregatedFeature = averageFeatures(all);
            } else {
                aggregatedFeature = feature;
            }

            String aggregatedJson = gson.toJson(aggregatedFeature);

            studentMapper.updateFaceFeature(studentId, aggregatedJson, newIndex);

            log.info("Face registered for student: {} (count: {})", studentCode, newIndex);
            return true;

        } catch (Exception e) {
            log.error("Error registering face for student: {}", studentId, e);
            return false;
        }
    }

    private float[] averageFeatures(float[][] features) {
        if (features == null || features.length == 0) {
            return new float[512];
        }

        int dim = features[0].length;
        float[] avg = new float[dim];

        for (float[] f : features) {
            for (int i = 0; i < dim; i++) {
                avg[i] += f[i];
            }
        }

        float norm = 0;
        for (float v : avg) {
            norm += v * v;
        }
        norm = (float) Math.sqrt(norm);
        if (norm > 0) {
            for (int i = 0; i < dim; i++) {
                avg[i] /= norm;
            }
        }

        return avg;
    }

    public int save(Student student) {
        if (student.getId() != null) {
            return studentMapper.update(student);
        } else {
            return studentMapper.insert(student);
        }
    }

    public int delete(Long id) {
        return studentMapper.deleteById(id);
    }

    public int countAll() {
        return studentMapper.countAll();
    }
}
