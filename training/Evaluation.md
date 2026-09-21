# Evaluation — Danh gia model sau training

## Purpose

Script va huong dan danh gia model: CER/WER tren test set, visualize errors, compare checkpoints.

## Scope

Evaluation pipeline: load checkpoint -> inference on test set -> compute CER/WER -> analyze.

## TODO

- [ ] Implement evaluation script (eval.py)
- [ ] Compute CER tren full test set
- [ ] Compute WER tren full test set
- [ ] Visualize worst-case predictions (anh + GT + predicted text)
- [ ] So sanh checkpoint theo epoch (learning curve)
- [ ] Export evaluation report (metrics.json + report.csv)

## References

- Training.md
- .ai/research/Evaluation.md
- .ai/research/CER.md
