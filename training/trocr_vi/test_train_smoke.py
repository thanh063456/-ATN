import os
import pytest
import tempfile
import pandas as pd
from PIL import Image
import torch
import sys
from pathlib import Path

# Need to import the script functions
sys.path.insert(0, str(Path(__file__).resolve().parent))

pytestmark = pytest.mark.smoke

@pytest.fixture
def mock_dataset(tmp_path):
    data_dir = tmp_path / "dataset"
    data_dir.mkdir()
    
    # Create dummy images
    img_dir = data_dir / "images"
    img_dir.mkdir()
    img_paths = []
    texts = []
    
    for i in range(50):
        img_path = img_dir / f"img_{i}.jpg"
        img = Image.new("RGB", (100, 30), color=(255, 255, 255))
        img.save(img_path)
        img_paths.append(str(img_path))
        texts.append(f"Mock text {i}")
        
    df = pd.DataFrame({"image_path": img_paths, "text": texts})
    df.to_csv(data_dir / "train_printed.tsv", sep="\t", index=False)
    df.head(10).to_csv(data_dir / "val_printed.tsv", sep="\t", index=False)
    
    return str(data_dir)

def test_trocr_smoke_training(mock_dataset, tmp_path, monkeypatch):
    try:
        import transformers
        import datasets
    except ImportError:
        pytest.skip("transformers or datasets not installed")
        
    from train_trocr_vi import main
        
    output_dir = tmp_path / "output"
    
    # Mock sys.argv
    test_args = [
        "train_trocr_vi.py",
        "--data_dir", mock_dataset,
        "--output_dir", str(output_dir),
        "--model", "small",  # Use small model for faster smoke test
        "--stage", "printed",
        "--max_samples", "50",
        "--epochs", "1",
    ]
    
    monkeypatch.setattr("sys.argv", test_args)
    
    # Run training
    main()
    
    # Verify outputs
    final_model_dir = output_dir / "final_model"
    assert final_model_dir.exists(), "Final model not saved"
    assert (final_model_dir / "config.json").exists()
    assert (final_model_dir / "pytorch_model.bin").exists() or (final_model_dir / "model.safetensors").exists()
    
    # Check generation and reload
    from transformers import VisionEncoderDecoderModel, TrOCRProcessor
    model = VisionEncoderDecoderModel.from_pretrained(str(final_model_dir))
    processor = TrOCRProcessor.from_pretrained(str(final_model_dir))
    
    # Mock inference
    img = Image.new("RGB", (100, 30), color=(255, 255, 255))
    pixel_values = processor(images=img, return_tensors="pt").pixel_values
    
    outputs = model.generate(pixel_values, max_new_tokens=10)
    decoded = processor.batch_decode(outputs, skip_special_tokens=True)
    
    assert isinstance(decoded[0], str)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
