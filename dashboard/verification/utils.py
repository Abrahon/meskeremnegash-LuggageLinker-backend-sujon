# verifications/utils.py
import requests
from PIL import Image
import pytesseract
from io import BytesIO
import re

def detect_document_type(cloudinary_url):
    # Download image from Cloudinary
    response = requests.get(cloudinary_url)
    img = Image.open(BytesIO(response.content))

    # Extract text
    text = pytesseract.image_to_string(img)

    # Check patterns
    if "PASSPORT" in text.upper() or "P<" in text:
        return "Passport"
    if "DRIVING" in text.upper() or "LICENSE" in text.upper():
        return "Driving License"
    if re.search(r"\b\d{10,17}\b", text):
        return "National ID"

    return "Unknown"
