import os
import json
import unicodedata
from PIL import Image, ImageOps
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Split
from tokenizers.normalizers import NFKC
from transformers import PreTrainedTokenizerFast

VIETNAMESE_CHARS = (
    "aàáảãạăằắẳẵặâầấẩẫậ"
    "b"
    "c"
    "dđ"
    "eèéẻẽẹêềếểễệ"
    "f"
    "g"
    "h"
    "iìíỉĩị"
    "j"
    "k"
    "l"
    "m"
    "n"
    "oòóỏõọôồốổỗộơờớởỡợ"
    "p"
    "q"
    "r"
    "s"
    "t"
    "uùúủũụưừứửữự"
    "v"
    "w"
    "x"
    "yỳýỷỹỵ"
    "z"
)
VIETNAMESE_CHARS += VIETNAMESE_CHARS.upper()
DIGITS = "0123456789"
PUNCTUATION = " .,:;!?'\"()[]{}-–—…+*/\\%=<>@#$&_~^|"

def build_vietnamese_vocab():
    """Builds a character-level vocabulary dictionary."""
    vocab = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3}
    idx = 4
    all_chars = list(set(VIETNAMESE_CHARS + DIGITS + PUNCTUATION))
    all_chars.sort()
    for char in all_chars:
        if char not in vocab:
            vocab[char] = idx
            idx += 1
    return vocab

def create_vi_tokenizer():
    """Creates a character-level PreTrainedTokenizerFast for Vietnamese."""
    vocab = build_vietnamese_vocab()
    
    # Create a tokenizers WordLevel model (using characters as words)
    tokenizer = Tokenizer(WordLevel(vocab=vocab, unk_token="<unk>"))
    tokenizer.normalizer = NFKC()
    
    # Split by character (each char is a token)
    # We use a regex that matches any single character
    tokenizer.pre_tokenizer = Split(pattern="", behavior="isolated")
    
    fast_tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=tokenizer,
        bos_token="<s>",
        eos_token="</s>",
        pad_token="<pad>",
        unk_token="<unk>",
    )
    return fast_tokenizer

def pad_image_to_square(image: Image.Image, target_size=384) -> Image.Image:
    """
    Pad image with white to a square without stretching.
    Then resize to target_size if needed.
    """
    w, h = image.size
    if w == h:
        sq_img = image
    else:
        max_dim = max(w, h)
        # Pad with white
        padding = (0, 0, max_dim - w, max_dim - h)
        fill_color: int | tuple[int, ...]
        if image.mode in ("L", "1"):
            fill_color = 255
        elif image.mode == "RGBA":
            fill_color = (255, 255, 255, 255)
        else:
            fill_color = (255, 255, 255)
        sq_img = ImageOps.expand(image, border=padding, fill=fill_color)
        
    if sq_img.size != (target_size, target_size):
        sq_img = sq_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    return sq_img

def chunk_long_line(image: Image.Image, text: str, max_chars: int = 25):
    """
    Mock implementation of chunking for long lines.
    In reality, we would need character/word bounding boxes to split the image accurately.
    For dataset preparation, if a string is too long, we might just drop or resize it.
    This function will be extended if word bounding boxes are available.
    """
    # Without layout coordinates, we can't accurately split an image horizontally.
    # The requirement: "chunk long lines at word gaps (<= ~20-25 chars), pad with white to a square"
    # To truly split an image by word gaps, we need a segmenter or we do naive horizontal splitting
    # based on character ratio, which is risky.
    # We will implement naive proportional splitting if aspect ratio > 3:1 for the baseline.
    
    w, h = image.size
    if len(text) <= max_chars or w / h <= 3.0:
        return [(image, text)]
        
    words = text.split()
    chunks = []
    
    current_words = []
    current_len = 0
    word_start_idx = 0
    
    for i, word in enumerate(words):
        if current_len + len(word) + 1 > max_chars and current_words:
            # Commit chunk
            chunk_text = " ".join(current_words)
            # Estimate width proportion
            total_chars = len(text)
            start_prop = word_start_idx / total_chars
            end_prop = (word_start_idx + len(chunk_text)) / total_chars
            
            crop_box = (int(w * start_prop), 0, int(w * end_prop), h)
            chunk_img = image.crop(crop_box)
            chunks.append((chunk_img, chunk_text))
            
            current_words = [word]
            current_len = len(word)
            word_start_idx += len(chunk_text) + 1 # +1 for space
        else:
            current_words.append(word)
            current_len += len(word) + (1 if current_words else 0)
            
    if current_words:
        chunk_text = " ".join(current_words)
        end_prop = 1.0
        start_prop = max(0.0, 1.0 - (len(chunk_text) / len(text)))
        crop_box = (int(w * start_prop), 0, w, h)
        chunk_img = image.crop(crop_box)
        chunks.append((chunk_img, chunk_text))
        
    return chunks
