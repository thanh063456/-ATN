# Elasticsearch — Thiết kế Search Engine

## Purpose

Nghiên cứu và thiết kế Elasticsearch cho hệ thống tìm kiếm tài liệu Student-Document-OCR:
index mapping, query strategies, Vietnamese text analysis, performance design.

## Scope

Elasticsearch 8.12.0: index design, document mapping, search queries, Vietnamese analyzer,
fuzzy search, highlight, aggregation, pagination.

---

## 1. Index Design

### Index name: `student_documents`

### Document Mapping

```json
{
  "mappings": {
    "properties": {
      "document_id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "[TBD — benchmark cần thiết]",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "[TBD — benchmark cần thiết]",
        "term_vector": "with_positions_offsets"
      },
      "content_corrected": {
        "type": "text",
        "analyzer": "[TBD]"
      },
      "category_code": {
        "type": "keyword"
      },
      "category_name": {
        "type": "text"
      },
      "student_id": {
        "type": "keyword"
      },
      "student_name": {
        "type": "text",
        "analyzer": "[TBD]"
      },
      "document_date": {
        "type": "date",
        "format": "yyyy-MM-dd"
      },
      "document_number": {
        "type": "keyword"
      },
      "uploader_id": {
        "type": "keyword"
      },
      "ocr_status": {
        "type": "keyword"
      },
      "ocr_confidence": {
        "type": "float"
      },
      "is_deleted": {
        "type": "boolean"
      },
      "created_at": {
        "type": "date"
      }
    }
  }
}
```

---

## 2. Vietnamese Analyzer Strategy

### Vấn đề với tiếng Việt

Tiếng Việt có đặc điểm:
- **Dấu thanh điệu**: 6 thanh (ngang, huyền, sắc, nặng, hỏi, ngã)
- **Từ ghép**: "sinh viên", "công tác" — không tách như tiếng Anh
- **Lỗi OCR phổ biến**: nhầm dấu (sắc ↔ huyền), thiếu dấu

### Analyzer Candidates

| Analyzer | Ưu | Nhược | Status |
|----------|-----|------|--------|
| `standard` | Đơn giản | Không hiểu tiếng Việt | Baseline |
| `icu_analyzer` (ICU plugin) | Unicode-aware, diacritic | Cần cài plugin | Candidate |
| Custom (whitespace + lowercase + ascii_folding) | Cho phép tìm không dấu | Mất ngữ nghĩa | Candidate |
| `vi_analyzer` | Tối ưu tiếng Việt | Chưa xác nhận tồn tại trong ES 8.x | [Cần kiểm tra] |

**[TBD — ADR-005]**: Cần benchmark với dữ liệu thực tế.

### Dự kiến Custom Analyzer

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "vietnamese_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding",
            "stop"
          ]
        },
        "vietnamese_search": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding"
          ]
        }
      }
    }
  }
}
```

> `asciifolding` cho phép tìm "sinh vien" ra được "sinh viên" — quan trọng cho OCR errors.

---

## 3. Search Queries

### 3.1 Full-text Search (Basic)

```json
{
  "query": {
    "multi_match": {
      "query": "{user_query}",
      "fields": ["title^2", "content", "student_name"],
      "type": "best_fields",
      "fuzziness": "AUTO"
    }
  }
}
```

### 3.2 Search với Filters

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "{user_query}",
            "fields": ["title^2", "content"],
            "fuzziness": "AUTO"
          }
        }
      ],
      "filter": [
        { "term": { "is_deleted": false } },
        { "term": { "ocr_status": "DONE" } },
        { "term": { "category_code": "{category}" } },
        {
          "range": {
            "created_at": {
              "gte": "{date_from}",
              "lte": "{date_to}"
            }
          }
        }
      ]
    }
  }
}
```

### 3.3 Fuzzy Search (cho lỗi OCR)

```json
{
  "query": {
    "fuzzy": {
      "content": {
        "value": "{keyword}",
        "fuzziness": 2,
        "max_expansions": 50,
        "prefix_length": 2
      }
    }
  }
}
```

### 3.4 Highlight Configuration

```json
{
  "highlight": {
    "fields": {
      "content": {
        "number_of_fragments": 3,
        "fragment_size": 150,
        "pre_tags": ["<em>"],
        "post_tags": ["</em>"]
      },
      "title": {
        "number_of_fragments": 0
      }
    }
  }
}
```

---

## 4. Pagination

```json
{
  "from": "{(page - 1) * page_size}",
  "size": "{page_size}",
  "track_total_hits": true
}
```

**Giới hạn:** `from + size ≤ 10.000` (ES default). Đủ cho use case của hệ thống.

---

## 5. Indexing Strategy

### Index sau OCR

Sau khi OCR hoàn thành:
```python
es.index(
    index="student_documents",
    id=document_id,
    document={
        "document_id": str(doc.id),
        "title": doc.title,
        "content": ocr_result.corrected_text or ocr_result.raw_text,
        "category_code": doc.category.code if doc.category else None,
        ...
    }
)
```

### Update khi user sửa OCR

```python
es.update(
    index="student_documents",
    id=document_id,
    doc={"content": corrected_text, "content_corrected": corrected_text}
)
```

### Soft delete

```python
es.update(
    index="student_documents",
    id=document_id,
    doc={"is_deleted": True}
)
```

---

## 6. Performance Considerations

| Concern | Giải pháp |
|---------|----------|
| Memory | ES sử dụng ~512MB–1GB RAM trong Docker |
| Indexing speed | Bulk indexing nếu import hàng loạt |
| Query speed | Shard 1, replica 0 (single node development) |
| Refresh interval | Default 1s (đủ cho use case) |

**Target latency:** p95 < 500ms cho search queries.

---

## 7. Không làm ở Phase 1

- Không tạo actual ES index
- Không chạy ES
- Không viết code Elasticsearch client

Những việc này thuộc **Phase 7 (Elasticsearch)**.

---

## TODO

- [ ] Cài Elasticsearch 8.12.0 và test benchmark analyzer (Phase 7)
- [ ] Quyết định ADR-005 (Vietnamese analyzer) sau benchmark
- [ ] Cài ICU Analysis Plugin và test với tài liệu CTSV mẫu
- [ ] Test fuzzy search với các lỗi OCR phổ biến trong tiếng Việt
- [ ] Measure query latency với 1k, 5k, 10k documents

## References

- https://www.elastic.co/guide/en/elasticsearch/reference/8.12/
- .ai/research/VietnameseSearch.md
- .ai/DECISIONS.md (ADR-004, ADR-005)
- .ai/design/API.md (Search group)
