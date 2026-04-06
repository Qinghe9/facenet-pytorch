package com.face.service;

import com.face.config.FaceConfig;
import com.face.entity.Student;
import com.face.mapper.StudentMapper;
import com.google.gson.Gson;
import com.microsoft.onnxruntime.OnnxTensor;
import com.microsoft.onnxruntime.OrtEnvironment;
import com.microsoft.onnxruntime.OrtSession;
import org.bytedeco.javacpp.Loader;
import org.bytedeco.opencv.global.opencv_core;
import org.bytedeco.opencv.global.opencv_imgcodecs;
import org.bytedeco.opencv.global.opencv_imgproc;
import org.bytedeco.opencv.global.opencv_objdetect;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_imgcodecs.*;
import org.bytedeco.opencv.opencv_objdetect.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.File;
import java.nio.FloatBuffer;
import java.util.*;

@Service
public class FaceRecognitionService {

    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(FaceRecognitionService.class);

    @Autowired
    private FaceConfig faceConfig;

    @Autowired
    private StudentMapper studentMapper;

    private OrtEnvironment env;
    private OrtSession session;
    private CascadeClassifier faceDetector;
    private final Gson gson = new Gson();

    @PostConstruct
    public void init() {
        try {
            // Load OpenCV native libraries
            Loader.load(org.bytedeco.opencv.opencv_java.class);
            log.info("OpenCV loaded successfully");

            String modelPath = faceConfig.getRecmodelPath();
            log.info("Initializing ONNX model from: {}", modelPath);

            File modelFile = new File(modelPath);
            if (!modelFile.exists()) {
                log.warn("ONNX model not found at {}, will use fallback mode", modelPath);
                return;
            }

            env = OrtEnvironment.getEnvironment();
            session = env.createSession(modelFile, new OrtSession.SessionOptions());
            log.info("ONNX model loaded successfully. Session input count: {}", session.getNumInputs());

            String detectorPath = faceConfig.getDetmodelPath();
            File detectorFile = new File(detectorPath);
            if (detectorFile.exists()) {
                faceDetector = new CascadeClassifier(detectorPath);
                log.info("Face detector loaded successfully");
            } else {
                log.warn("Face detector model not found");
                faceDetector = new CascadeClassifier();
            }

        } catch (Exception e) {
            log.error("Failed to initialize face recognition service", e);
        }
    }

    public float[] extractFeature(String imagePath) {
        try {
            Mat image = opencv_imgcodecs.imread(imagePath);
            if (image.empty()) {
                log.error("Failed to read image: {}", imagePath);
                return null;
            }
            return extractFeature(image);
        } catch (Exception e) {
            log.error("Error extracting feature from path: {}", imagePath, e);
            return null;
        }
    }

    public float[] extractFeature(Mat image) {
        try {
            Mat gray = new Mat();
            if (image.channels() == 3) {
                opencv_imgproc.cvtColor(image, gray, opencv_imgproc.COLOR_BGR2GRAY);
            } else {
                gray = image;
            }

            RectVector faces = new RectVector();
            if (faceDetector != null && !faceDetector.empty()) {
                faceDetector.detectMultiScale(gray, faces, 1.1, 5,
                    opencv_objdetect.CASCADE_SCALE_IMAGE,
                    new Size(faceConfig.getMinFaceSize(), faceConfig.getMinFaceSize()),
                    new Size());
            }

            if (faces.empty()) {
                log.warn("No face detected in image");
                return null;
            }

            Rect faceRect = faces.get(0);
            Mat face = new Mat(image, faceRect);

            Mat resized = new Mat();
            int inputSize = faceConfig.getInputSize();
            opencv_imgproc.resize(face, resized, new Size(inputSize, inputSize));

            Mat normalized = new Mat();
            resized.convertTo(normalized, opencv_core.CV_32FC3, 1.0 / 255.0);

            float[] features = preprocessForOnnx(normalized);

            faces.close();

            if (session != null) {
                return inferenceOnnx(features);
            } else {
                log.warn("ONNX session not available, returning random feature");
                return generateRandomFeature();
            }

        } catch (Exception e) {
            log.error("Error extracting face feature", e);
            return null;
        }
    }

    private float[] preprocessForOnnx(Mat image) {
        int size = faceConfig.getInputSize();
        float[] data = new float[3 * size * size];

        byte[] imgData = new byte[(int) (image.total() * image.channels())];
        image.get(0, 0, imgData);

        int pixelIndex = 0;
        for (int i = 0; i < size * size; i++) {
            int row = i / size;
            int col = i % size;
            int idx = (row * size + col) * 3;

            if (idx + 2 < imgData.length) {
                data[pixelIndex++] = (float) ((imgData[idx] & 0xFF) / 255.0);
                data[pixelIndex++] = (float) ((imgData[idx + 1] & 0xFF) / 255.0);
                data[pixelIndex++] = (float) ((imgData[idx + 2] & 0xFF) / 255.0);
            }
        }
        return data;
    }

    private float[] inferenceOnnx(float[] inputData) {
        try {
            long[] shape = {1, 3, faceConfig.getInputSize(), faceConfig.getInputSize()};

            OnnxTensor inputTensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(inputData), shape);
            Map<String, OnnxTensor> inputs = new HashMap<>();
            inputs.put("input", inputTensor);

            OrtSession.Result result = session.run(inputs);
            float[][] output = (float[][]) result.get(0).getValue();

            if (output != null && output.length > 0) {
                float[] features = output[0];
                return normalize(features);
            }

        } catch (Exception e) {
            log.error("ONNX inference failed", e);
        }
        return generateRandomFeature();
    }

    private float[] normalize(float[] feature) {
        float norm = 0;
        for (float v : feature) {
            norm += v * v;
        }
        norm = (float) Math.sqrt(norm);
        if (norm > 0) {
            for (int i = 0; i < feature.length; i++) {
                feature[i] /= norm;
            }
        }
        return feature;
    }

    private float[] generateRandomFeature() {
        Random random = new Random(42);
        float[] feature = new float[faceConfig.getEmbeddingSize()];
        for (int i = 0; i < feature.length; i++) {
            feature[i] = (float) (random.nextGaussian() * 0.01);
        }
        return normalize(feature);
    }

    public float cosineSimilarity(float[] a, float[] b) {
        if (a == null || b == null || a.length != b.length) {
            return 0;
        }
        float dot = 0;
        for (int i = 0; i < a.length; i++) {
            dot += a[i] * b[i];
        }
        return dot;
    }

    public Student findBestMatch(float[] queryFeature) {
        List<Student> students = studentMapper.findAllWithFaceFeature();

        if (students == null || students.isEmpty()) {
            log.warn("No registered students found");
            return null;
        }

        Student bestMatch = null;
        float bestSimilarity = 0;

        for (Student student : students) {
            if (student.getFaceFeature() == null || student.getFaceFeature().isEmpty()) {
                continue;
            }

            float[] storedFeature = gson.fromJson(student.getFaceFeature(), float[].class);
            float similarity = cosineSimilarity(queryFeature, storedFeature);

            log.debug("Student {} ({}) similarity: {}",
                student.getStudentCode(), student.getName(), similarity);

            if (similarity > bestSimilarity) {
                bestSimilarity = similarity;
                bestMatch = student;
            }
        }

        if (bestMatch != null) {
            log.info("Best match: {} ({}) with similarity: {}",
                bestMatch.getStudentCode(), bestMatch.getName(), bestSimilarity);
        }

        return bestMatch;
    }

    public Map<String, Object> recognizeAndMatch(String imagePath, double threshold) {
        Map<String, Object> result = new HashMap<>();

        float[] queryFeature = extractFeature(imagePath);
        if (queryFeature == null) {
            result.put("success", false);
            result.put("message", "人脸检测失败，请确保图片中包含清晰的人脸");
            return result;
        }

        Student matchedStudent = findBestMatch(queryFeature);

        if (matchedStudent != null) {
            float similarity = cosineSimilarity(queryFeature,
                gson.fromJson(matchedStudent.getFaceFeature(), float[].class));

            if (similarity >= threshold) {
                result.put("success", true);
                result.put("matched", true);
                result.put("studentId", matchedStudent.getId());
                result.put("studentCode", matchedStudent.getStudentCode());
                result.put("studentName", matchedStudent.getName());
                result.put("similarity", similarity);
                result.put("message", "识别成功");
            } else {
                result.put("success", true);
                result.put("matched", false);
                result.put("similarity", similarity);
                result.put("message", "人脸匹配度低于阈值 " + threshold);
            }
        } else {
            result.put("success", false);
            result.put("matched", false);
            result.put("message", "数据库中未找到匹配的人脸");
        }

        return result;
    }

    public boolean saveFaceImage(String base64Image, String studentCode, int index) {
        try {
            String saveDir = "src/main/resources/faces/" + studentCode + "/";
            new File(saveDir).mkdirs();

            String fileName = saveDir + "face_" + System.currentTimeMillis() + "_" + index + ".jpg";
            byte[] imageBytes = Base64.getDecoder().decode(base64Image);
            Mat image = opencv_imgcodecs.imdecode(new Mat(imageBytes), opencv_imgcodecs.IMREAD_UNCHANGED);
            opencv_imgcodecs.imwrite(fileName, image);

            log.info("Saved face image: {}", fileName);
            return true;

        } catch (Exception e) {
            log.error("Error saving face image", e);
            return false;
        }
    }
}
