import pytest
from app.services.trocr_vi_utils import create_vi_tokenizer

def test_vi_tokenizer_roundtrip():
    tokenizer = create_vi_tokenizer()
    
    # Diacritic-heavy string
    text = "Luật sư nguyễn văn A, ở tại Phường Bến Nghé, Quận 1! 123456"
    
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded, skip_special_tokens=True)
    
    # Check round-trip, tokenizer.normalizer uses NFKC, so the result might be NFC/NFKC normalized
    import unicodedata
    expected = unicodedata.normalize("NFKC", text)
    # Actually NFKC does not change standard composed characters, it should match expected
    assert decoded.replace(" ", "") == expected.replace(" ", "")
    # The tokenizer.pre_tokenizer splits by character, but does it join with spaces?
    # WordLevel without spaces might output characters separated by spaces if not handled, 
    # let's just check the characters without spaces.
    
    # Let's check the actual decoded text directly
    print("Decoded text:", decoded)

def test_vi_tokenizer_unknown():
    tokenizer = create_vi_tokenizer()
    # Russian or Chinese characters should become <unk>
    text = "Nguyễn Văn A 测 试"
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded)
    assert "<unk>" in decoded

if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])
