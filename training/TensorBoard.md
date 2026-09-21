# TensorBoard — Monitoring Training

## Purpose

Huong dan su dung TensorBoard de monitor training: loss, metrics, learning rate, predictions.

## Scope

Log training loss, validation CER/WER, learning rate, sample predictions vao TensorBoard.

## TODO

- [ ] Setup TensorBoard SummaryWriter (log_dir=runs/)
- [ ] Log training loss va validation loss moi step/epoch
- [ ] Log CER/WER metrics moi validation epoch
- [ ] Log learning rate schedule
- [ ] Log sample predictions (add_image: original + predicted text)
- [ ] Huong dan truy cap TensorBoard UI (tensorboard --logdir runs/)
- [ ] Huong dan export scalars sang CSV de phan tich

## References

- Training.md
- Evaluation.md
- https://www.tensorflow.org/tensorboard
