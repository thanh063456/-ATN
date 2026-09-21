# Transfer Learning — Học Chuyển giao trong Fine-tuning OCR

## Purpose

Nghiên cứu áp dụng kỹ thuật Transfer Learning (Học chuyển giao) để fine-tune mô hình VietOCR pre-trained trên tập dữ liệu đặc thù Công tác sinh viên với chi phí tính toán thấp nhất.

## Scope

Chiến lược Freeze Layers, Learning Rate Scheduling, và giải pháp tránh Overfitting.

---

## 1. Nguyên lý Transfer Learning với VietOCR

Mô hình VietOCR pre-trained (`vgg_transformer.pth`) đã được huấn luyện trên hàng triệu dòng chữ tiếng Việt thông thường.
- **CNN Backbone (VGG)**: Đã học tốt các đặc trưng thị giác cấp thấp (nét chữ, cạnh, góc). -> **Freeze 80% CNN Layers**.
- **Transformer Encoder & Decoder**: Cần fine-tune nhẹ để thích nghi với bố cục văn bản, từ vựng và font chữ đặc thù của các biểu mẫu đơn từ CTSV.

```
┌─────────────────────────────────┐
│ CNN Backbone (VGG)              │ -> Freeze (Không update weights)
└────────────────┬────────────────┘
                 │ Features
                 ▼
┌─────────────────────────────────┐
│ Transformer Seq2Seq Model       │ -> Unfreeze & Fine-tune (Unfrozen Layer)
└─────────────────────────────────┘
```

---

## 2. Chiến lược Tối ưu Hóa (Optimization Policy)

1. **Low Learning Rate**: Dùng $LR = 10^{-4}$ (thay vì $10^{-3}$ khi train from scratch) để tránh phá hỏng kiến thức đã học.
2. **Cosine Annealing Learning Rate**: Giảm dần LR theo đường cong Cosine giúp mô hình hội tụ mịn vào điểm tối ưu cục bộ tốt hơn.
3. **Early Stopping**: Ngừng huấn luyện nếu `val_CER` không giảm sau 5 Epochs liên tiếp.

---

## TODO

- [ ] Thực nghiệm so sánh giữa Fine-tune toàn bộ mô hình (Full Tuning) vs Fine-tune Transformer Decoder (Freeze CNN).
- [ ] Ghi nhận thời gian huấn luyện và lượng GPU VRAM tiêu thụ vào `docs/Experiment.md`.

## References

- VietOCR.md
- Training.md
- Evaluation.md
