# Training Script — Huong dan Training

## Purpose

Chi tiet training script: config file, training loop, loss function, optimizer, scheduler.

## Scope

Training loop voi CTC Loss hoac Cross-Entropy, AdamW optimizer, CosineAnnealingLR.

## TODO

- [ ] Viet training config (YAML: model, data, optimizer, scheduler, logging)
- [ ] Implement training loop (forward, loss, backward, optimizer step)
- [ ] Implement validation step (compute CER/WER moi N epochs)
- [ ] Implement gradient clipping (max_norm=1.0)
- [ ] Implement learning rate scheduler (CosineAnnealingLR hoac OneCycleLR)
- [ ] Implement TensorBoard va WandB logging
- [ ] Implement model checkpointing (save best CER)

## References

- Dataset.md
- Evaluation.md
- Checkpoint.md
- TensorBoard.md
