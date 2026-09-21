# Vietnamese Search — Xử lý Tiếng Việt cho Tìm kiếm Elasticsearch

## Purpose

Nghiên cứu các phương pháp và cấu hình NLP tiếng Việt trong Elasticsearch nhằm tối ưu hóa tìm kiếm full-text trên dữ liệu OCR.

## Scope

Character Folding (loại bỏ dấu), Custom Tokenizer/Analyzer, Synonym Filters và Fuzzy matching xử lý sai sót OCR.

---

## 1. Thách thức đối với Tìm kiếm Văn bản Tiếng Việt OCR

1. **Dấu thanh điệu**: Người dùng muốn tìm "don xin nghi hoc" vẫn phải ra kết quả "Đơn xin nghỉ học tạm thời".
2. **Lỗi OCR nhỏ**: OCR bị nhầm 1-2 ký tự (vd: "báo lưu" thay vì "bảo lưu").
3. **Từ ghép tiếng Việt**: Tiếng Việt phân cách từ bằng khoảng trắng nhưng nhiều từ mang ý nghĩa ghép (vd: "Công tác sinh viên").

---

## 2. Giải pháp Cấu hình Custom Analyzer trong Elasticsearch

Sử dụng kết hợp `standard tokenizer` + `lowercase filter` + `asciifolding filter` (chuyển ký tự có dấu về không dấu):

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "vi_search_analyzer": {
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

---

## 3. Chiến lược Query phối hợp (Multi-Match & Fuzzy)

```json
{
  "query": {
    "bool": {
      "should": [
        {
          "match_phrase": {
            "content": {
              "query": "nghỉ học tạm thời",
              "boost": 5
            }
          }
        },
        {
          "multi_match": {
            "query": "nghi hoc tam thoi",
            "fields": ["title^3", "content^1"],
            "fuzziness": "AUTO",
            "prefix_length": 2
          }
        }
      ]
    }
  }
}
```

---

## TODO

- [ ] Thực hiện Benchmark so sánh `ICU Analyzer` vs `Custom Asciifolding Analyzer` ở Phase 7.
- [ ] Xây dựng danh sách Từ đồng nghĩa (Synonyms) cho thuật ngữ hành chính CTSV.

## References

- Elasticsearch.md
- API.md
- .ai/design/Search.md
