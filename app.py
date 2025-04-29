import cv2
import pytesseract
import numpy as np
import base64
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import io
from PIL import Image
import re

app = FastAPI()

class ImagePayload(BaseModel):
    image_base64: str

def preprocess_image(image_bytes):
    image = np.array(Image.open(io.BytesIO(image_bytes)))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    denoised = cv2.medianBlur(thresh, 3)
    return denoised

def extract_text(image):
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    return text

def parse_lab_tests(text):
    lines = text.split('\n')
    lab_tests = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r'([A-Za-z\s\(\)\-]+)\s+([\d\.]+)\s*([a-zA-Z\/%]*)\s*([\d\.]+\s*-\s*[\d\.]+)?', line)
        if match:
            test_name = match.group(1).strip()
            test_value = match.group(2)
            test_unit = match.group(3)
            ref_range = match.group(4)

            if ref_range:
                ref_range = ref_range.replace(" ", "")
                try:
                    lower, upper = map(float, ref_range.split('-'))
                    lab_test_out_of_range = not (lower <= float(test_value) <= upper)
                except:
                    lab_test_out_of_range = None
            else:
                lab_test_out_of_range = None

            lab_tests.append({
                "test_name": test_name,
                "test_value": test_value,
                "bio_reference_range": ref_range if ref_range else "",
                "test_unit": test_unit,
                "lab_test_out_of_range": lab_test_out_of_range
            })

    return lab_tests

@app.post("/get-lab-tests")
async def get_lab_tests(payload: ImagePayload):
    try:
        image_data = base64.b64decode(payload.image_base64)
        preprocessed_image = preprocess_image(image_data)
        extracted_text = extract_text(preprocessed_image)
        lab_tests = parse_lab_tests(extracted_text)

        return JSONResponse(content={
            "is_success": True,
            "data": lab_tests
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
