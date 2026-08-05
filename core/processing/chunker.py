from transformers import AutoTokenizer
from config import EMBED_MODEL_PATH, EMBED_MODEL_NAME
import torch
import re
import os

def load_tokenizer():

    if os.path.isdir(EMBED_MODEL_PATH):

        print("Loading tokenizer locally")

        tokenizer = AutoTokenizer.from_pretrained(
            EMBED_MODEL_PATH
        )

    else:

        print("Downloading tokenizer")

        tokenizer = AutoTokenizer.from_pretrained(
            EMBED_MODEL_NAME
        )

        tokenizer.save_pretrained(
            EMBED_MODEL_PATH
        )

    return tokenizer
    
_tokenizer = None

def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = load_tokenizer()
    return _tokenizer

def clean_chunk(text):

    # normalize whitespace from chunk joins
    text = re.sub(r'\s+', ' ', text)

    # fix spacing before punctuation
    # "model ." → "model."
    text = re.sub(r'\s+\.', '.', text)

    # fix spacing around commas
    text = re.sub(r'\s+,', ',', text)

    # fix chunk boundary hyphen splits
    # "embed- ding" → "embedding"
    text = re.sub(r'(\w)- (\w)', r'\1\2', text)

    return text.strip()



def create_chunks(text, tokenizer=None):
    if tokenizer is None:
        tokenizer = get_tokenizer()
        
    text = " ".join(text)

    encodings = tokenizer(
        text,
        max_length=400,
        truncation=True,
        stride=50,
        return_overflowing_tokens=True,
        return_tensors=None
    )

    chunks = [
        tokenizer.decode(ids)
        for ids in encodings["input_ids"]
    ]

    chunks = [clean_chunk(text) for text in chunks]

    return chunks
