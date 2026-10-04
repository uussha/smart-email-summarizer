import re
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

app = FastAPI(title="Smart Email Summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 150
    min_length: int = 30


model_name = "sshleifer/distilbart-cnn-12-6"
tokenizer = None
model = None


def get_model_components():
    global tokenizer, model
    if tokenizer is None or model is None:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def calculate_reduction(original_words: int, summary_words: int) -> float:
    if original_words <= 0:
        return 0.0
    return round(((original_words - summary_words) / original_words) * 100, 1)


def preprocess_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    lines: List[str] = []
    skip_signature = False
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines and lines[-1] != "":
                lines.append("")
            continue

        if re.match(r"^(from|to|cc|bcc|subject|date)\s*:", stripped, re.IGNORECASE):
            continue
        if stripped.startswith(">"):
            continue
        if re.match(r"^on .+ wrote:$", stripped, re.IGNORECASE):
            continue
        if re.match(r"^(best|regards|thanks|sincerely|cheers)[,\-:]?$", stripped, re.IGNORECASE):
            skip_signature = True
            continue
        if skip_signature:
            continue

        lines.append(stripped)

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)
    return cleaned


def split_into_chunks(text: str, max_words: int = 400) -> List[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()] if text.strip() else []

    chunks = []
    for start in range(0, len(words), max_words):
        chunk_words = words[start:start + max_words]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def summarize_text(text: str, max_length: int = 150, min_length: int = 30) -> str:
    tokenizer_obj, model_obj = get_model_components()
    cleaned_text = preprocess_text(text)
    if not cleaned_text or len(cleaned_text) < 20:
        return ""

    chunked_text = split_into_chunks(cleaned_text)
    if len(chunked_text) == 1:
        inputs = tokenizer_obj(cleaned_text, return_tensors="pt", truncation=True)
        output_tokens = model_obj.generate(
            **inputs,
            max_length=max_length,
            min_length=min_length,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
        return tokenizer_obj.decode(output_tokens[0], skip_special_tokens=True).strip()

    chunk_summaries = []
    for chunk in chunked_text:
        inputs = tokenizer_obj(chunk, return_tensors="pt", truncation=True)
        output_tokens = model_obj.generate(
            **inputs,
            max_length=max(max_length // 2, 60),
            min_length=max(min_length // 2, 20),
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
        summary = tokenizer_obj.decode(output_tokens[0], skip_special_tokens=True).strip()
        if summary:
            chunk_summaries.append(summary)

    combined_text = " \n".join(chunk_summaries)
    if not combined_text:
        return ""

    inputs = tokenizer_obj(combined_text, return_tensors="pt", truncation=True)
    output_tokens = model_obj.generate(
        **inputs,
        max_length=max_length,
        min_length=min_length,
        no_repeat_ngram_size=3,
        early_stopping=True,
    )
    return tokenizer_obj.decode(output_tokens[0], skip_special_tokens=True).strip()


@app.get("/")
def health_check():
    return {"status": "ready", "message": "Smart Email Summarizer backend is running."}


@app.post("/summarize")
def summarize(request: SummarizeRequest):
    text = request.text.strip()
    if not text or len(text) < 20:
        return {"summary": "", "error": "Please provide a longer email or article text to summarize."}

    cleaned_text = preprocess_text(text)
    if not cleaned_text:
        return {"summary": "", "error": "Please provide a longer email or article text to summarize."}

    summary = summarize_text(cleaned_text, max_length=request.max_length, min_length=request.min_length)
    original_words = count_words(cleaned_text)
    summary_words = count_words(summary)
    reduction_percentage = calculate_reduction(original_words, summary_words)

    return {
        "summary": summary,
        "original_word_count": original_words,
        "summary_word_count": summary_words,
        "reduction_percentage": reduction_percentage,
    }
