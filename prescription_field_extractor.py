#!/usr/bin/env python3
"""
Advanced Prescription Field Extractor
Based on CEO's schema requirements for prescription data extraction
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

class PrescriptionFieldExtractor:
    """
    Extract structured prescription fields according to the company schema
    """
    
    def __init__(self):
        self.schema = {
            "patient_name": {"type": "string", "max_length": 100, "required": True},
            "patient_address": {"type": "string", "max_length": 255, "required": False},
            "patient_dob": {"type": "date", "max_length": None, "required": True},
            "patient_age": {"type": "integer", "max_length": None, "required": True},
            "patient_sex": {"type": "string", "max_length": 10, "required": True},
            "prescription_date": {"type": "date", "max_length": None, "required": True},
            "doctor_name": {"type": "string", "max_length": 100, "required": True},
            "doctor_title": {"type": "string", "max_length": 100, "required": True},
            "clinic_address": {"type": "string", "max_length": 255, "required": False},
            "clinic_phone": {"type": "string", "max_length": 20, "required": True},
            "medicine_name": {"type": "string", "max_length": 100, "required": True},
            "medicine_dose": {"type": "string", "max_length": 50, "required": True},
            "medicine_frequency": {"type": "string", "max_length": 20, "required": False},
            "medicine_duration": {"type": "string", "max_length": 50, "required": True},
            "instructions": {"type": "text", "max_length": 500, "required": True},
            "immunization": {"type": "string", "max_length": 100, "required": False},
            "immunization_date": {"type": "date", "max_length": None, "required": False},
            "is_allergic": {"type": "boolean", "max_length": None, "required": False},
            "weight": {"type": "string", "max_length": None, "required": False},
            "is_pregnant": {"type": "boolean", "max_length": None, "required": False}
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned
    
    def extract_patient_name(self, text: str) -> str:
        """Extract patient name"""
        patterns = [
            r"FOR.*?\(.*?\)\s*([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)",  # FOR (...) John R. Doe
            r"Patient.*?[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
            r"Name.*?[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
            r"([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+),\s+\w+,\s+\w+"  # John R. Doe, HM3, USN
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = self.clean_text(match.group(1))
                # Remove military ranks/titles
                name = re.sub(r',\s*(HM\d+|USN|USNR|MD|DR\.?).*?$', '', name, flags=re.IGNORECASE)
                return name.strip()
        return ""
    
    def extract_dates(self, text: str) -> Dict[str, str]:
        """Extract various dates from prescription"""
        dates = {"prescription_date": "", "patient_dob": "", "immunization_date": ""}
        
        # Prescription date patterns
        prescription_patterns = [
            r"DATE\s+(\d{1,2}\s+\w{3}\s+\d{2,4})",  # DATE 23 JAN 99
            r"(?:PRESCRIPTION|RX).*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
            r"(\d{1,2}\s+\w{3,9}\s+\d{4})"  # 23 January 1999
        ]
        
        for pattern in prescription_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates["prescription_date"] = self.clean_text(match.group(1))
                break
        
        # DOB patterns
        dob_patterns = [
            r"DOB[:\-\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
            r"Birth.*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
            r"Born.*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})"
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates["patient_dob"] = self.clean_text(match.group(1))
                break
        
        return dates
    
    def extract_patient_demographics(self, text: str) -> Dict[str, Any]:
        """Extract patient demographic information"""
        demographics = {"patient_age": "", "patient_sex": "", "weight": ""}
        
        # Age extraction
        age_patterns = [
            r"Age[:\-\s]+(\d{1,3})",
            r"(\d{1,3})\s*y(?:ears?)?\.?\s*old",
            r"(?:under|age)\s+(\d{1,3})"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                demographics["patient_age"] = int(match.group(1))
                break
        
        # Gender extraction
        gender_patterns = [
            r"(?:Sex|Gender)[:\-\s]+(Male|Female|M|F)",
            r"\b(Male|Female|M|F)\b"
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).upper()
                if gender in ['M', 'MALE']:
                    demographics["patient_sex"] = "Male"
                elif gender in ['F', 'FEMALE']:
                    demographics["patient_sex"] = "Female"
                break
        
        # Weight extraction
        weight_patterns = [
            r"Weight[:\-\s]+(\d+(?:\.\d+)?)\s*(kg|lbs?|pounds?)",
            r"(\d+(?:\.\d+)?)\s*(kg|lbs?|pounds?)"
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                demographics["weight"] = f"{match.group(1)} {match.group(2)}"
                break
        
        return demographics
    
    def extract_doctor_info(self, text: str) -> Dict[str, str]:
        """Extract doctor information"""
        doctor_info = {"doctor_name": "", "doctor_title": ""}
        
        # Doctor name and title patterns
        doctor_patterns = [
            r"([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)\s+((?:LODR\.|MD|DR\.?|USNR|DDS|DO|NP|PA).*?)(?:\s|$)",
            r"(?:Dr\.?|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
            r"SIGNATURE.*?([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)"
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doctor_info["doctor_name"] = self.clean_text(match.group(1))
                if len(match.groups()) > 1:
                    doctor_info["doctor_title"] = self.clean_text(match.group(2))
                break
        
        return doctor_info
    
    def extract_clinic_info(self, text: str) -> Dict[str, str]:
        """Extract clinic/facility information"""
        clinic_info = {"clinic_address": "", "clinic_phone": ""}
        
        # Clinic address patterns
        address_patterns = [
            r"MEDICAL FACILITY\s+(.*?)(?=DATE|$)",
            r"(?:Clinic|Hospital|Facility)[:\-\s]+(.*?)(?:\n|$)",
            r"U\.S\.S\.\s+(.*?)\s+\([^)]+\)"
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                clinic_info["clinic_address"] = self.clean_text(match.group(1))
                break
        
        # Phone number patterns
        phone_patterns = [
            r"(?:Phone|Tel|Call)[:\-\s]*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                clinic_info["clinic_phone"] = self.clean_text(match.group(1))
                break
        
        return clinic_info
    
    def extract_medication_info(self, text: str) -> Dict[str, str]:
        """Extract medication information"""
        med_info = {
            "medicine_name": "",
            "medicine_dose": "",
            "medicine_frequency": "",
            "medicine_duration": "",
            "instructions": ""
        }
        
        # Medicine name and dose patterns
        medicine_patterns = [
            r"(?:Tr|Rx)\s+(\w+)\s+(\d+\s*ml)",  # Tr Belledenna 15 ml
            r"(\w+)\s+(\w+)\s+(\d+\s*ml)",  # Amphogel gaad 120 ml
            r"(\w+)\s+(\d+\s*(?:mg|ml|g|tablets?))"
        ]
        
        medicines = []
        doses = []
        
        for pattern in medicine_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    medicines.append(match.group(1))
                    doses.append(match.group(2) if len(match.groups()) == 2 else match.group(3))
        
        if medicines:
            med_info["medicine_name"] = ", ".join(set(medicines))  # Remove duplicates
            med_info["medicine_dose"] = ", ".join(doses)
        
        # Frequency patterns
        frequency_patterns = [
            r"(\d+\+\d+\+\d+)",  # 1+1+1
            r"(\d+)\s*times?\s*(?:per\s*)?day",
            r"every\s+(\d+)\s*hours?"
        ]
        
        for pattern in frequency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                med_info["medicine_frequency"] = match.group(1)
                break
        
        # Duration patterns
        duration_patterns = [
            r"for\s+(\d+\s*(?:days?|weeks?|months?))",
            r"(\d+\s*(?:days?|weeks?|months?))\s*course"
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                med_info["medicine_duration"] = match.group(1)
                break
        
        # Instructions patterns
        instruction_patterns = [
            r"(?:Seg|Signa)[:\-\s]*(.*?)(?:\n|$)",
            r"Instructions[:\-\s]*(.*?)(?:\n|$)",
            r"Take\s+(.*?)(?:\n|$)"
        ]
        
        for pattern in instruction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                med_info["instructions"] = self.clean_text(match.group(1))
                break
        
        return med_info
    
    def extract_special_conditions(self, text: str) -> Dict[str, Any]:
        """Extract allergy, pregnancy, and immunization info"""
        conditions = {
            "is_allergic": None,
            "is_pregnant": None,
            "immunization": "",
            "immunization_date": ""
        }
        
        # Allergy patterns
        if re.search(r"allerg", text, re.IGNORECASE):
            conditions["is_allergic"] = True
        elif re.search(r"no.*?allerg", text, re.IGNORECASE):
            conditions["is_allergic"] = False
        
        # Pregnancy patterns
        if re.search(r"pregnan", text, re.IGNORECASE):
            conditions["is_pregnant"] = True
        elif re.search(r"not.*?pregnan", text, re.IGNORECASE):
            conditions["is_pregnant"] = False
        
        # Immunization patterns
        vaccine_patterns = [
            r"(?:Vaccine|Immunization|Vaccination)[:\-\s]+(\w+(?:\s+\w+)*)",
            r"(\w+)\s+vaccine"
        ]
        
        for pattern in vaccine_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                conditions["immunization"] = self.clean_text(match.group(1))
                break
        
        return conditions
    
    def validate_and_format_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format fields according to schema"""
        validated_fields = {}
        
        for field_name, value in fields.items():
            if field_name in self.schema:
                field_schema = self.schema[field_name]
                
                # Handle empty values
                if not value and value != 0 and value is not False:
                    validated_fields[field_name] = "" if field_schema["type"] in ["string", "text", "date"] else None
                    continue
                
                # Type validation and formatting
                if field_schema["type"] == "string" or field_schema["type"] == "text":
                    validated_value = str(value)
                    if field_schema["max_length"] and len(validated_value) > field_schema["max_length"]:
                        validated_value = validated_value[:field_schema["max_length"]]
                    validated_fields[field_name] = validated_value
                elif field_schema["type"] == "integer":
                    try:
                        validated_fields[field_name] = int(value) if value else None
                    except (ValueError, TypeError):
                        validated_fields[field_name] = None
                elif field_schema["type"] == "boolean":
                    validated_fields[field_name] = value if isinstance(value, bool) else None
                elif field_schema["type"] == "date":
                    validated_fields[field_name] = str(value) if value else ""
                else:
                    validated_fields[field_name] = value
            else:
                validated_fields[field_name] = value
        
        return validated_fields
    
    def extract_all_fields(self, ocr_text: str) -> Dict[str, Any]:
        """Extract all prescription fields from OCR text"""
        # Initialize empty fields
        prescription_data = {field: "" for field in self.schema.keys()}
        
        # Clean input text
        text = self.clean_text(ocr_text)
        
        # Extract each category of information
        prescription_data["patient_name"] = self.extract_patient_name(text)
        
        dates = self.extract_dates(text)
        prescription_data.update(dates)
        
        demographics = self.extract_patient_demographics(text)
        prescription_data.update(demographics)
        
        doctor_info = self.extract_doctor_info(text)
        prescription_data.update(doctor_info)
        
        clinic_info = self.extract_clinic_info(text)
        prescription_data.update(clinic_info)
        
        medication_info = self.extract_medication_info(text)
        prescription_data.update(medication_info)
        
        special_conditions = self.extract_special_conditions(text)
        prescription_data.update(special_conditions)
        
        # Validate and format according to schema
        return self.validate_and_format_fields(prescription_data)
    
    def get_field_completion_status(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Get completion status for each field"""
        status = {
            "total_fields": len(self.schema),
            "completed_fields": 0,
            "required_fields": 0,
            "required_completed": 0,
            "field_status": {}
        }
        
        for field_name, field_schema in self.schema.items():
            is_required = field_schema["required"]
            has_value = bool(fields.get(field_name))
            
            status["field_status"][field_name] = {
                "required": is_required,
                "completed": has_value,
                "value": fields.get(field_name, "")
            }
            
            if has_value:
                status["completed_fields"] += 1
            
            if is_required:
                status["required_fields"] += 1
                if has_value:
                    status["required_completed"] += 1
        
        status["completion_percentage"] = (status["completed_fields"] / status["total_fields"]) * 100
        status["required_completion_percentage"] = (status["required_completed"] / status["required_fields"]) * 100 if status["required_fields"] > 0 else 0
        
        return status

# Example usage function
def process_prescription_image(ocr_text: str) -> Dict[str, Any]:
    """Process prescription image and return structured data"""
    extractor = PrescriptionFieldExtractor()
    
    # Extract fields
    prescription_fields = extractor.extract_all_fields(ocr_text)
    
    # Get completion status
    completion_status = extractor.get_field_completion_status(prescription_fields)
    
    return {
        "prescription_data": prescription_fields,
        "completion_status": completion_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test with existing OCR result
    try:
        with open("ocr_result.txt", "r", encoding="utf-8") as f:
            ocr_text = f.read()
        
        result = process_prescription_image(ocr_text)
        
        print("="*80)
        print("ADVANCED PRESCRIPTION FIELD EXTRACTION")
        print("="*80)
        print(f"Completion: {result['completion_status']['completion_percentage']:.1f}%")
        print(f"Required Fields: {result['completion_status']['required_completion_percentage']:.1f}%")
        print("="*80)
        
        # Save enhanced results
        with open("prescription_enhanced.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("Enhanced extraction saved to: prescription_enhanced.json")
        
    except FileNotFoundError:
        print("OCR result file not found. Run the OCR extraction first.")