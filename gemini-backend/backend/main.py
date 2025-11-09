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
    cardCount: int = Form(...),
    quizCount: int = Form(5)   # ✅ NEW
):
    text = extract_text_from_file(file)

    # ✅ FLASHCARD PROMPT (unchanged — EXACT behavior preserved)
    flash_prompt = f"""
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

    # ✅ QUIZ PROMPT — SAME AS COLAB FORMAT
    quiz_prompt = f"""
You are an expert quiz-maker.
Analyze the provided text and generate {quizCount} multiple-choice quiz questions.

You MUST:
- Return a valid JSON list ONLY
- NO text before/after JSON
- Each question must contain:
  • "question"
  • "options" → list of 4 strings
  • "answer" → must be ONE of the options

Example:
[
  {{
    "question": "What is the primary function of a CPU?",
    "options": ["Store data", "Perform calculations", "Render graphics", "Connect to WiFi"],
    "answer": "Perform calculations"
  }}
]

TEXT:
---
{text}
---
"""

    ### ✅ ---- FLASHCARDS ----
    response_fc = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[flash_prompt]
    )

    raw_fc = response_fc.text
    print("\n===== RAW FLASHCARD OUTPUT =====")
    print(raw_fc)
    print("===== END RAW =====\n")

    match_fc = re.search(r"\[.*\]", raw_fc, re.DOTALL)
    if match_fc:
        try:
            flashcards = json.loads(match_fc.group(0))
        except:
            flashcards = []
    else:
        flashcards = []

    ### ✅ ---- QUIZ ----
    response_q = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[quiz_prompt]
    )

    raw_q = response_q.text
    print("\n===== RAW QUIZ OUTPUT =====")
    print(raw_q)
    print("===== END RAW =====\n")

    match_q = re.search(r"\[.*\]", raw_q, re.DOTALL)
    if match_q:
        try:
            quiz = json.loads(match_q.group(0))
        except:
            quiz = []
    else:
        quiz = []

    ### ✅ Return BOTH
    return {
        "flashcards": flashcards,
        "quiz": quiz
    }
