import os
import random
import uuid
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path

# Vietnamese administrative text samples
TEXT_SAMPLES = [
    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "Độc lập - Tự do - Hạnh phúc",
    "Số: 1413/TB-ĐHĐL",
    "Lâm Đồng, ngày 26 tháng 8 năm 2025",
    "THÔNG BÁO",
    "Về việc nộp học phí học kỳ I năm học 2025-2026",
    "Kính gửi: Các khoa, phòng ban, và toàn thể sinh viên",
    "Căn cứ Quyết định số 123/QĐ-ĐHĐL ngày 01/01/2025",
    "Phòng Công tác Sinh viên thông báo",
    "Mức thu học phí tín chỉ: 350.000 VNĐ/tín chỉ",
    "Sinh viên nộp tiền vào tài khoản nhà trường",
    "Tên tài khoản: TRƯỜNG ĐẠI HỌC ĐÀ LẠT",
    "Số tài khoản: 123456789 tại Ngân hàng Agribank",
    "Nguyễn Văn A - MSSV: 20123456",
    "Chủ tịch Hội đồng Quản trị",
    "Lưu ý: Hạn chót nộp là 15/09/2025."
]

def apply_augmentations(img: Image.Image) -> Image.Image:
    # 1. Blur
    if random.random() > 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.5)))
    # 2. Noise (scan shading)
    if random.random() > 0.5:
        noise = Image.effect_noise(img.size, random.randint(10, 50)).convert("RGB")
        img = Image.blend(img, noise, alpha=random.uniform(0.05, 0.2))
    # 3. Small rotation
    if random.random() > 0.5:
        angle = random.uniform(-2, 2)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    # 4. Contrast
    if random.random() > 0.5:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.5, 1.5))
    return img

def main():
    out_dir = Path(__file__).resolve().parent.parent.parent / "dataset" / "synth_crops"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to load Arial or similar from Windows fonts
    font_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\times.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    
    fonts = []
    for fp in font_paths:
        if os.path.exists(fp):
            fonts.append(fp)
            
    if not fonts:
        print("No valid fonts found. Cannot generate synthetic text with diacritics using default font.")
        return
        
    records = []
    
    num_samples = 200
    for i in range(num_samples):
        text = random.choice(TEXT_SAMPLES)
        font_path = random.choice(fonts)
        font_size = random.randint(24, 36)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            continue
            
        # Get text bounding box
        left, top, right, bottom = font.getbbox(text)
        w, h = right - left, bottom - top
        
        # Add padding
        pad = random.randint(5, 20)
        img_w, img_h = w + pad*2, h + pad*2
        
        img = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        text_color = (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50))
        draw.text((pad - left, pad - top), text, font=font, fill=text_color)
        
        img = apply_augmentations(img)
        
        # Red stamp overlay randomly
        if random.random() > 0.8:
            stamp = Image.new("RGBA", img.size, (255, 255, 255, 0))
            stamp_draw = ImageDraw.Draw(stamp)
            stamp_draw.ellipse([pad, pad, img_w-pad, img_h-pad], outline=(200, 0, 0, 128), width=3)
            img.paste(stamp, (0, 0), stamp)
            
        file_name = f"synth_{uuid.uuid4().hex[:8]}.jpg"
        file_path = out_dir / file_name
        
        # Save as JPEG with random quality to simulate compression
        img.save(file_path, "JPEG", quality=random.randint(50, 95))
        
        records.append({
            "image_path": str(file_path),
            "text": text,
            "domain": "printed_synth",
            "doc_id": "SYNTH001"
        })
        
    df = pd.DataFrame(records)
    df.to_csv(out_dir.parent / "synth_manifest.tsv", sep="\t", index=False)
    print(f"Generated {len(records)} synthetic lines in {out_dir}")

if __name__ == "__main__":
    main()
