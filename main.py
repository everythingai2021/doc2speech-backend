from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pyt2s.services import stream_elements
import os
import io
import string
import PyPDF2

import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pdf2tts.onrender.com"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"Hello": "World"}

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        return {"error": "File must be a PDF"}

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            pdf_path = temp_pdf.name
            contents = await file.read()
            temp_pdf.write(contents)

        extracted_text = extract_text(pdf_path)

        if len(extracted_text.strip()) == 0:
            return {"error": "No extractable text found in the PDF."}

        data = stream_elements.requestTTS(extracted_text, stream_elements.Voice.Amy.value)

        return StreamingResponse(
            io.BytesIO(data),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=output.mp3"}
        )
    except Exception as e:
        return {"error": f"An error occurred while processing the PDF: {str(e)}"}

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    
     

        


def clean_text(text):
    allowed = string.ascii_letters + string.digits + string.punctuation + " \n"
    strings = [[]]
    idx = 0
    for c in text:
        if c in allowed:
            if c == "\n":
                strings[idx].append(".")
                strings[idx].append(c)
                idx += 1
                strings.append([])
            else:
                strings[idx].append(c)
    res = ""
    for s in strings:
        res += "".join(s)
    return res

def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += clean_text(page_text) + "\n"
            else:
                text += "[No text found on this page]\n"
    return text

