from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os, json, re
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ FILE → TEXT EXTRACTION
def extract_text_from_file(file: UploadFile):
    if file.content_type == "application/pdf":
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file.file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif file.content_type == "text/plain":
        return file.file.read().decode("utf-8")

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")


# ✅ MAIN ENDPOINT
@app.post("/api/generate")
async def generate(
    file: UploadFile = File(...),
    cardCount: int = Form(...)
):
    text = extract_text_from_file(file)

    # ✅ strict JSON prompt
    full_prompt = f"""
You are an expert educational assistant. Your task is to generate flashcards based on the provided text.

REQUIREMENTS:
- Generate up to {cardCount} flashcards.
- Each flashcard MUST have "question" and "answer".
- KEY: RETURN ONLY A JSON ARRAY. NO prose. NO markdown. NO labels.
- If fewer quality flashcards exist, return fewer.
- FORMAT:

[
  {{"question":"...", "answer":"..."}},
  {{"question":"...", "answer":"..."}}
]

TEXT:
---
{text}
---
"""

    # ✅ call Gemini
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[full_prompt]
    )

    raw = response.text
    print("\n===== RAW GEMINI OUTPUT =====")
    print(raw)
    print("===== END RAW =====\n")

    # ✅ CLEAN JSON EXTRACTION
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        # return raw so frontend/dev can see
        return {"error": "No JSON found in model output", "raw": raw}

    json_text = match.group(0)

    try:
        data = json.loads(json_text)
    except:
        return {"error": "JSON parsing failed", "raw": raw}

    return data
