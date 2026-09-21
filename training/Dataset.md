# Training Dataset — Chuan bi du lieu huan luyen

## Purpose

Huong dan chuan bi dataset cho training: format, split, augmentation, data loader.

## Scope

Dataset format, train/val/test split, image augmentation pipeline, custom PyTorch Dataset class.

## TODO

- [ ] Dinh nghia dataset format (image file + text label file pairs)
- [ ] Script tao train/val/test split (80/10/10)
- [ ] Implement PyTorch Dataset class (ImageTextDataset)
- [ ] Implement augmentation pipeline (albumentations: rotate, blur, noise, distort)
- [ ] Implement DataLoader voi batching va collate_fn
- [ ] Visualize sample batch de kiem tra pipeline

## References

- .ai/research/Dataset.md
- Training.md
- dataset/README.md
