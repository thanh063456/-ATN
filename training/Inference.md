# Inference — Chay model inference

## Purpose

Huong dan chay inference: single image, batch, optimization (ONNX, TorchScript).

## Scope

Inference tu checkpoint hoac exported model. Tich hop vao backend service.

## TODO

- [ ] Implement single image inference (infer.py)
- [ ] Implement batch inference voi batching de toi uu throughput
- [ ] Xu ly preprocessing trong inference (resize, normalize)
- [ ] Export sang ONNX format (torch.onnx.export)
- [ ] Benchmark inference latency (CPU vs GPU, batch_size=1 vs 8)
- [ ] Implement confidence score output
- [ ] Tich hop voi backend OCR service

## References

- Training.md
- Checkpoint.md
- backend/Architecture.md
