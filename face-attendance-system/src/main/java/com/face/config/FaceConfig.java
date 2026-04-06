package com.face.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "face.model")
public class FaceConfig {
    private String detmodelPath;
    private String recmodelPath;
    private Integer embeddingSize = 512;
    private Double similarityThreshold = 0.6;
    private Integer minFaceSize = 40;
    private Integer inputSize = 160;

    public String getDetmodelPath() { return detmodelPath; }
    public void setDetmodelPath(String detmodelPath) { this.detmodelPath = detmodelPath; }
    public String getRecmodelPath() { return recmodelPath; }
    public void setRecmodelPath(String recmodelPath) { this.recmodelPath = recmodelPath; }
    public Integer getEmbeddingSize() { return embeddingSize; }
    public void setEmbeddingSize(Integer embeddingSize) { this.embeddingSize = embeddingSize; }
    public Double getSimilarityThreshold() { return similarityThreshold; }
    public void setSimilarityThreshold(Double similarityThreshold) { this.similarityThreshold = similarityThreshold; }
    public Integer getMinFaceSize() { return minFaceSize; }
    public void setMinFaceSize(Integer minFaceSize) { this.minFaceSize = minFaceSize; }
    public Integer getInputSize() { return inputSize; }
    public void setInputSize(Integer inputSize) { this.inputSize = inputSize; }
}
