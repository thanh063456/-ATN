import time
import glob
import torch
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer

model_name = "./models/trocr-vi/final_model"
proc = ViTImageProcessor.from_pretrained(model_name)
tok = AutoTokenizer.from_pretrained(model_name)

print("Loading FP16 model on CUDA...")
model = VisionEncoderDecoderModel.from_pretrained(model_name).half().to("cuda")
model.eval()

crops = [Image.open(p).convert("RGB") for p in sorted(glob.glob("dataset/line_crops/0_1395*/*.png"))[:16]]

# Warmup
pix = proc(images=crops[:2], return_tensors="pt").pixel_values.half().to("cuda")
with torch.inference_mode():
    _ = model.generate(pix, max_new_tokens=64, num_beams=1)

# Benchmark Greedy (beams=1)
t0 = time.perf_counter()
pix = proc(images=crops, return_tensors="pt").pixel_values.half().to("cuda")
with torch.inference_mode():
    gen1 = model.generate(pix, max_new_tokens=128, num_beams=1, do_sample=False)
t1 = time.perf_counter()
preds1 = tok.batch_decode(gen1, skip_special_tokens=True)

print(f"FP16 Greedy (beams=1) for 16 lines: {t1 - t0:.2f}s ({((t1 - t0)/16):.3f}s/line)")
for i, p in enumerate(preds1[:3]):
    print(f"  Line {i+1}: {p}")
