# ==============================================================================
# docker/elasticsearch/Dockerfile — Elasticsearch 8 with Vietnamese NLP Plugins
# DocuCTSV — Hệ thống Số hóa & OCR Hồ sơ Sinh viên (Đại học Đà Lạt)
# ==============================================================================

FROM docker.elastic.co/elasticsearch/elasticsearch:8.12.0

USER root

# Cài đặt plugin phân tích tiếng Việt ICU (International Components for Unicode)
RUN bin/elasticsearch-plugin install --batch analysis-icu

# Cài đặt plugin phân tách từ phức tiếng Việt (Vietnamese Analysis) nếu khả dụng
# Plugin cho phép phân đoạn từ ghép: "học bổng" -> "học_bổng", "miễn giảm" -> "miễn_giảm"
RUN bin/elasticsearch-plugin install --batch https://github.com/duydo/elasticsearch-analysis-vietnamese/releases/download/v8.12.0/elasticsearch-analysis-vietnamese-8.12.0.zip || \
    echo "Warning: elasticsearch-analysis-vietnamese prebuilt binary not available for this exact patch; falling back to ICU + custom Lucene Shingle compound analyzer."

# Phân quyền thư mục cho user elasticsearch
RUN chown -R elasticsearch:elasticsearch /usr/share/elasticsearch

USER elasticsearch

# Cấu hình biến môi trường JVM
ENV ES_JAVA_OPTS="-Xms1g -Xmx1g"

