# Training Scripts — Script huan luyen

## Purpose

Mo ta va huong dan cac script lien quan den training: run, resume, export.

## Scope

Scripts: train.py, resume_training.py, export_onnx.py, benchmark_inference.py.

## TODO

- [ ] Viet train.py voi argparse (--config, --resume, --device)
- [ ] Viet resume_training.py (load checkpoint va tiep tuc)
- [ ] Viet export_onnx.py (xuat model sang ONNX)
- [ ] Viet benchmark_inference.py (do latency tren CPU/GPU)
- [ ] Document CLI args cho tung script

## References

- training/Training.md
- training/Checkpoint.md
- Makefile
