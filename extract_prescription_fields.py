#!/usr/bin/env python3
import base64
import os
import json
import re
from datetime import datetime
from mistralai import Mistral

def extract_prescription_fields(ocr_text):
    """
    Extract structured prescription fields from OCR text according to the schema
    """
    # Initialize the prescription data structure
    prescription_data = {
        "patient_name": "",
        "patient_address": "",
        "patient_dob": "",
        "patient_age": "",
        "patient_sex": "",
        "prescription_date": "",
        "doctor_name": "",
        "doctor_title": "",
        "clinic_address": "",
        "clinic_phone": "",
        "medicine_name": "",
        "medicine_dose": "",
        "medicine_frequency": "",
        "medicine_duration": "",
        "instructions": "",
        "immunization": "",
        "immunization_date": "",
        "is_allergic": None,
        "weight": "",
        "is_pregnant": None
    }
    
    # Clean the OCR text
    text = ocr_text.strip()
    
    # Extract Patient Name
    name_patterns = [
        r"FOR.*?(\w+\s+\w+\.\s+\w+)",  # FOR John R. Doe
        r"Patient.*?:?\s*([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)",
        r"Name.*?:?\s*([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prescription_data["patient_name"] = match.group(1).strip()
            break
    
    # Extract Prescription Date
    date_patterns = [
        r"DATE\s+(\d{1,2}\s+\w{3}\s+\d{2,4})",  # DATE 23 JAN 99
        r"(\d{1,2}\s+\w{3}\s+\d{2,4})",  # 23 JAN 99
        r"(\d{1,2}/\d{1,2}/\d{2,4})",  # 23/01/99
        r"(\d{4}-\d{2}-\d{2})"  # 1999-01-23
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prescription_data["prescription_date"] = match.group(1).strip()
            break
    
    # Extract Doctor Name and Title
    doctor_patterns = [
        r"([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)\s+(LODR\.\s+MD\.\s+USNR)",  # Jack R. Frost LODR. MD. USNR
        r"Dr\.?\s+([A-Z][a-z]+\s+[A-Z]?\.\?\s*[A-Z][a-z]+)",
        r"SIGNATURE.*?([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)\s+(.*?MD.*?)"
    ]
    
    for pattern in doctor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prescription_data["doctor_name"] = match.group(1).strip()
            if len(match.groups()) > 1:
                prescription_data["doctor_title"] = match.group(2).strip()
            break
    
    # Extract Medical Facility/Clinic
    facility_patterns = [
        r"MEDICAL FACILITY\s+(.*?)(?=DATE|$)",
        r"U\.S\.S\.\s+(.*?)\s+\(DD\s+\d+\)"
    ]
    
    for pattern in facility_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prescription_data["clinic_address"] = match.group(1).strip()
            break
    
    # Extract Medicine Information
    medicine_patterns = [
        r"Tr\s+(\w+)\s+(\d+\s*ml)",  # Tr Belledenna 15 ml
        r"(\w+)\s+(\w+)\s+(\d+\s*ml)"  # Amphogel gaad 120 ml
    ]
    
    medicines = []
    doses = []
    
    for pattern in medicine_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 2:
                medicines.append(match.group(1))
                doses.append(match.group(2))
    
    if medicines:
        prescription_data["medicine_name"] = ", ".join(medicines)
        prescription_data["medicine_dose"] = ", ".join(doses)
    
    # Extract Instructions
    instruction_patterns = [
        r"Seg:\s*(.*?)(?=\n|$)",  # Seg: 5ml lid a.c.
        r"Signa.*?Seg:\s*(.*?)(?=\n|$)"
    ]
    
    for pattern in instruction_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prescription_data["instructions"] = match.group(1).strip()
            break
    
    # Extract Lot Number and Expiration (additional info)
    lot_match = re.search(r"LOT NO:\s*(\w+)", text, re.IGNORECASE)
    exp_match = re.search(r"EXP DATE:\s*(\d{2}/\d{2})", text, re.IGNORECASE)
    
    additional_info = []
    if lot_match:
        additional_info.append(f"Lot: {lot_match.group(1)}")
    if exp_match:
        additional_info.append(f"Exp: {exp_match.group(1)}")
    
    if additional_info:
        if prescription_data["instructions"]:
            prescription_data["instructions"] += " | " + " | ".join(additional_info)
        else:
            prescription_data["instructions"] = " | ".join(additional_info)
    
    return prescription_data

def extract_text_and_fields_from_image(image_path, api_key):
    """
    Extract text from image and parse prescription fields
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None, None
    
    # Read and encode the image
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Determine MIME type
        file_ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if file_ext == ".png" else "image/jpeg"
        
        # Create Mistral client
        client = Mistral(api_key=api_key)
        
        # Prepare document for OCR
        document = {
            "type": "image_url", 
            "image_url": f"data:{mime_type};base64,{encoded_image}"
        }
        
        print(f"Processing image: {os.path.basename(image_path)}")
        print("Extracting text using Mistral OCR...")
        
        # Process OCR
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest", 
            document=document, 
            include_image_base64=True
        )
        
        # Extract text from response
        pages = ocr_response.pages if hasattr(ocr_response, "pages") else (ocr_response if isinstance(ocr_response, list) else [])
        raw_text = "\n\n".join(page.markdown for page in pages) or "No text found."
        
        # Extract structured fields
        prescription_fields = extract_prescription_fields(raw_text)
        
        return raw_text, prescription_fields
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None

def main():
    # Image path
    image_path = r"c:\ICEL_TECH_WORKSPACE\Mistral-OCR-\A-sample-prescription-image-in-grayscale-version.png"
    
    # Get API key
    api_key = os.getenv('MISTRAL_API_KEY')
    
    if not api_key:
        print("Please set your Mistral API key as an environment variable:")
        print("Set MISTRAL_API_KEY=your_api_key_here")
        print("\nOr enter it now:")
        api_key = input("Enter your Mistral API Key: ").strip()
        
    if not api_key:
        print("Error: No API key provided!")
        return
    
    # Extract text and fields
    raw_text, prescription_fields = extract_text_and_fields_from_image(image_path, api_key)
    
    if raw_text and prescription_fields:
        print("\n" + "="*80)
        print("RAW EXTRACTED TEXT:")
        print("="*80)
        print(raw_text)
        
        print("\n" + "="*80)
        print("STRUCTURED PRESCRIPTION FIELDS:")
        print("="*80)
        
        # Display structured data
        for field, value in prescription_fields.items():
            status = "✅" if value else "❌"
            print(f"{status} {field.replace('_', ' ').title()}: {value if value else 'Not found'}")
        
        print("="*80)
        
        # Save raw text
        with open("ocr_result.txt", "w", encoding="utf-8") as f:
            f.write(raw_text)
        
        # Save structured data as JSON
        with open("prescription_fields.json", "w", encoding="utf-8") as f:
            json.dump(prescription_fields, f, indent=2, ensure_ascii=False)
        
        # Save structured data as formatted text
        with open("prescription_structured.txt", "w", encoding="utf-8") as f:
            f.write("PRESCRIPTION DATA EXTRACTION RESULTS\n")
            f.write("="*50 + "\n\n")
            for field, value in prescription_fields.items():
                f.write(f"{field.replace('_', ' ').title()}: {value if value else 'Not found'}\n")
        
        print(f"\nFiles saved:")
        print(f"📄 Raw OCR text: ocr_result.txt")
        print(f"📊 Structured JSON: prescription_fields.json")
        print(f"📋 Formatted data: prescription_structured.txt")
        
    else:
        print("Failed to extract text from image.")

if __name__ == "__main__":
    main()