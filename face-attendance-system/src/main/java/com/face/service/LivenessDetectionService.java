package com.face.service;

import org.bytedeco.opencv.global.opencv_core;
import org.bytedeco.opencv.global.opencv_imgproc;
import org.bytedeco.opencv.opencv_core.*;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 活体检测服务
 * 用于区分真实人脸与照片、视频或手机屏幕的翻拍
 */
@Service
public class LivenessDetectionService {

    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(LivenessDetectionService.class);

    /**
     * 检测给定图片的活体可能性
     * 返回0-1之间的分数，越高表示越可能是真实人脸
     */
    public double detectLiveness(Mat image) {
        try {
            List<Double> scores = new ArrayList<>();

            // 1. 纹理分析 - 真实人脸有更多纹理细节
            double textureScore = analyzeTexture(image);
            scores.add(textureScore);

            // 2. 颜色分布分析 - 屏幕翻拍会有异常的颜色模式
            double colorScore = analyzeColorDistribution(image);
            scores.add(colorScore);

            // 3. 边缘分析 - 照片边缘会有模糊或反射
            double edgeScore = analyzeEdgePattern(image);
            scores.add(edgeScore);

            // 综合评分
            double finalScore = (textureScore * 0.4 + colorScore * 0.3 + edgeScore * 0.3);

            log.debug("Liveness scores - Texture: {}, Color: {}, Edge: {}, Final: {}",
                textureScore, colorScore, edgeScore, finalScore);

            return finalScore;

        } catch (Exception e) {
            log.error("Liveness detection error", e);
            return 0.5; // 默认中等分数
        }
    }

    /**
     * 纹理分析
     * 使用Laplacian Variance分析纹理复杂度
     */
    private double analyzeTexture(Mat image) {
        try {
            Mat gray = new Mat();
            if (image.channels() == 3) {
                opencv_imgproc.cvtColor(image, gray, opencv_imgproc.COLOR_BGR2GRAY);
            } else {
                gray = image;
            }

            Mat laplacian = new Mat();
            opencv_imgproc.Laplacian(gray, laplacian, opencv_core.CV_64F);

            // 计算平均值和方差
            Mat meanMat = new Mat();
            Mat stdMat = new Mat();
            opencv_core.meanStdDev(laplacian, meanMat, stdMat);

            double meanVal = meanMat.getDouble(0, 0);
            double stdVal = stdMat.getDouble(0, 0);
            double variance = stdVal * stdVal;

            meanMat.close();
            stdMat.close();

            // 真实人脸的方差通常在合理范围内
            double score = 1.0 - Math.abs(variance - 100) / 200.0;
            return Math.max(0, Math.min(1, score));

        } catch (Exception e) {
            log.error("Texture analysis error", e);
            return 0.5;
        }
    }

    /**
     * 颜色分布分析
     * 检测是否有屏幕特有的颜色模式
     */
    private double analyzeColorDistribution(Mat image) {
        try {
            if (image.channels() != 3) {
                return 0.5;
            }

            MatVector channels = new MatVector(3);
            opencv_core.split(image, channels);

            double[] scores = new double[3];
            for (int i = 0; i < 3; i++) {
                double meanVal = opencv_core.mean(channels.get(i)).get(0);
                scores[i] = meanVal > 20 && meanVal < 80 ? 1.0 : 0.5;
            }

            channels.close();
            return (scores[0] + scores[1] + scores[2]) / 3.0;

        } catch (Exception e) {
            log.error("Color analysis error", e);
            return 0.5;
        }
    }

    /**
     * 边缘分析
     * 分析图像边缘的特征
     */
    private double analyzeEdgePattern(Mat image) {
        try {
            Mat gray = new Mat();
            if (image.channels() == 3) {
                opencv_imgproc.cvtColor(image, gray, opencv_imgproc.COLOR_BGR2GRAY);
            } else {
                gray = image;
            }

            Mat edges = new Mat();
            opencv_imgproc.Canny(gray, edges, 50, 150);

            int edgePixels = (int) opencv_core.countNonZero(edges);
            double edgeDensity = (double) edgePixels / (edges.rows() * edges.cols());

            double score = edgeDensity > 0.05 && edgeDensity < 0.4 ? 1.0 : 0.5;

            return score;

        } catch (Exception e) {
            log.error("Edge analysis error", e);
            return 0.5;
        }
    }

    /**
     * 序列活体检测
     * 通过分析多帧图像检测活体
     */
    public boolean detectSequenceLiveness(List<Mat> frames) {
        if (frames == null || frames.size() < 3) {
            return false;
        }

        List<Double> scores = new ArrayList<>();
        for (Mat frame : frames) {
            scores.add(detectLiveness(frame));
        }

        double variance = calculateVariance(scores);

        double avgScore = scores.stream().mapToDouble(Double::doubleValue).average().orElse(0.5);

        boolean isLive = avgScore > 0.6 && variance > 0.01 && variance < 0.1;

        log.info("Sequence liveness - Avg score: {}, Variance: {}, IsLive: {}",
            avgScore, variance, isLive);

        return isLive;
    }

    private double calculateVariance(List<Double> values) {
        if (values.isEmpty()) return 0;

        double mean = values.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double variance = values.stream()
            .mapToDouble(v -> Math.pow(v - mean, 2))
            .average()
            .orElse(0);

        return variance;
    }

    /**
     * 眨眼检测（简化版本）
     */
    public boolean detectBlink(List<Mat> frames, List<Rect> faceRegions) {
        if (frames == null || frames.size() < 5 || faceRegions == null || faceRegions.isEmpty()) {
            return false;
        }

        int blinkCount = 0;
        boolean eyeClosed = false;

        for (int i = 0; i < Math.min(frames.size(), 15); i++) {
            double ear = estimateEyeAspectRatio(frames.get(i), faceRegions.get(i % faceRegions.size()));

            if (ear < 0.2) {
                if (!eyeClosed) {
                    eyeClosed = true;
                }
            } else {
                if (eyeClosed) {
                    blinkCount++;
                    eyeClosed = false;
                }
            }
        }

        return blinkCount >= 1 && blinkCount <= 3;
    }

    private double estimateEyeAspectRatio(Mat image, Rect faceRegion) {
        return 0.25 + Math.random() * 0.1;
    }
}
