# Checkpoint — Quan ly model checkpoint

## Purpose

Huong dan luu va load model checkpoint: naming convention, best model selection, versioning.

## Scope

Checkpoint naming: epoch_{N:03d}_cer_{CER:.4f}.pth. Save: model state, optimizer, epoch, metrics.

## TODO

- [ ] Dinh nghia checkpoint naming convention
- [ ] Implement save_checkpoint(model, optimizer, epoch, metrics, path)
- [ ] Implement load_checkpoint(path) -> returns model, optimizer, epoch
- [ ] Implement best model tracking (theo CER thap nhat)
- [ ] Implement checkpoint pruning (giu top-3 checkpoints)
- [ ] Document checkpoint metadata (training config, dataset info, metrics)

## References

- Training.md
- Inference.md
- models/README.md
