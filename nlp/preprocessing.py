import fitz
import re

def extract_text(pdf_path):

    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        text.append(page.get_text("text"))

    text = "\n".join(text)

    # Fix Broken hyphenated words
    text = re.sub(r'-\n','',text)

    return text
    

def tokenize_lines(text):

    lines = text.split("\n")

    return [line.strip() for line in lines]


def clean_lines(lines):

    cleaned = []

    for line in lines:

        if len(line.split()) < 5:
            continue

        # normalize whitespace
        line = re.sub(r'\s+', ' ', line)

        # remove citations like [12]
        line = re.sub(r'\[\d+\]', '', line)

        # remove isolated numbers but keep model numbers
        line = re.sub(r'\b\d+\b(?=[^\-/])', '', line)

        # remove figure/table refs
        line = re.sub(r'(Figure|Table)\s+\d+', '', line)

        # remove weird symbols 
        line = re.sub(r'[^\w\s\-\.:,()%/\+]', ' ', line)

        # remove urls 
        line = re.sub(r'http\S+|www\S+', '', line)       

        # fix hyphen broken words
        line = re.sub(r'(\w)-\s+(\w)', r'\1\2', line)

        # remove very short tokens (like z, b, ψ fragments)
        words = [
            w for w in line.split()
            if len(w) > 1
        ]

        line = " ".join(words)

        line = line.strip()

        cleaned.append(line)

    return cleaned

def lines_to_paragraph(lines):

    paragraphs = []
    current_para = []

    for line in lines:

        #empty line = paragraph boundary
        if line == "":
            if current_para:
                paragraphs.append(" ".join(current_para))

                current_para = []
        else :
            current_para.append(line)
        
    # Last paragraph
    if current_para:
        paragraphs.append(" ".join(current_para))

    return paragraphs

def clean_paragraphs(paragraphs):
    STOPWORDS = {
    "the","is","are","was","were","of","in",
    "on","for","to","with","and","a","an",
    "by","from","that","this","we","our"
    }

    cleaned = []

    for para in paragraphs:

        words = para.split()

        # Remove very short fragments
        if len(words) < 4:
            continue

        # Remove numeric heavy lines
        digit_ratio = sum(c.isdigit() for c in para) / len(para)

        if digit_ratio > 0.3:
            continue

        # Remove symbol heavy lines
        alpha_ratio = sum(c.isalpha() for c in para) / len(para)

        if alpha_ratio < 0.5:
            continue

        # require at least one stopword (VERY effective)
        if not any(word in STOPWORDS for word in words):
            continue

        cleaned.append(para)

    # Second pass: merge small paragraphs

    merged = []

    i = 0

    while i < len(cleaned):

        para = cleaned[i]

        words = para.split()

        # If paragraph is small
        if len(words) < 15 or len(para) < 100:

            if i+1 < len(cleaned):

                combined = para + " " + cleaned[i+1]

                merged.append(combined)

                i += 2

                continue

        merged.append(para)

        i += 1


    return merged


def preprocess_paper(pdf_path):

    text = extract_text(pdf_path)
    lines = tokenize_lines(text)
    lines = clean_lines(lines)
    paragraphs = lines_to_paragraph(lines)
    paragraphs = clean_paragraphs(paragraphs)

    return paragraphs
