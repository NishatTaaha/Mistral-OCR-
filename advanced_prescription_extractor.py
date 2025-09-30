#!/usr/bin/env python3
"""
Advanced Prescription Field Extractor using Multiple AI Approaches
Combines LangChain, Structured Output, and Enhanced Pattern Matching
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Check if optional dependencies are available
try:
    from langchain_community.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.output_parsers import PydanticOutputParser
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Fallback to older import
        from langchain.llms import OpenAI
        from langchain.prompts import PromptTemplate
        from langchain.output_parsers import PydanticOutputParser
        from pydantic import BaseModel, Field
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        print("LangChain not available. Install with: pip install langchain-community openai pydantic")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("SpaCy not available. Install with: pip install spacy")

from mistralai import Mistral

class PrescriptionData(BaseModel):
    """Pydantic model for structured prescription data validation"""
    patient_name: Optional[str] = Field(description="Full name of the patient")
    patient_address: Optional[str] = Field(description="Address of the patient")
    patient_dob: Optional[str] = Field(description="Date of birth (DD/MM/YYYY or similar)")
    patient_age: Optional[int] = Field(description="Age of the patient in years")
    patient_sex: Optional[str] = Field(description="Gender: Male, Female, M, F")
    prescription_date: Optional[str] = Field(description="Date when prescription was written")
    doctor_name: Optional[str] = Field(description="Name of the prescribing doctor")
    doctor_title: Optional[str] = Field(description="Medical title or specialty of doctor")
    clinic_address: Optional[str] = Field(description="Address of the clinic or hospital")
    clinic_phone: Optional[str] = Field(description="Phone number of the clinic")
    medicine_name: Optional[str] = Field(description="Name(s) of prescribed medication(s)")
    medicine_dose: Optional[str] = Field(description="Dosage and concentration")
    medicine_frequency: Optional[str] = Field(description="How often to take (e.g., 2x daily)")
    medicine_duration: Optional[str] = Field(description="How long to take the medication")
    instructions: Optional[str] = Field(description="Special instructions from doctor")
    immunization: Optional[str] = Field(description="Name of vaccine if given")
    immunization_date: Optional[str] = Field(description="Date vaccine was administered")
    is_allergic: Optional[bool] = Field(description="Whether patient has allergies")
    weight: Optional[str] = Field(description="Patient weight with unit")
    is_pregnant: Optional[bool] = Field(description="Whether patient is pregnant")

class AdvancedPrescriptionExtractor:
    """Advanced prescription field extractor using multiple AI techniques"""
    
    def __init__(self, mistral_api_key: str, openai_api_key: Optional[str] = None):
        self.mistral_client = Mistral(api_key=mistral_api_key)
        self.openai_api_key = openai_api_key
        
        # Initialize extraction methods
        self.extraction_methods = []
        
        # Add Mistral structured extraction
        self.extraction_methods.append(self._mistral_structured_extraction)
        
        # Add LangChain extraction if available
        if LANGCHAIN_AVAILABLE and openai_api_key:
            self.extraction_methods.append(self._langchain_extraction)
        
        # Add NLP extraction if SpaCy is available
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.extraction_methods.append(self._nlp_extraction)
            except OSError:
                print("SpaCy English model not found. Install with: python -m spacy download en_core_web_sm")
        
        # Always include enhanced regex as fallback
        self.extraction_methods.append(self._enhanced_regex_extraction)
        
        self.schema = {
            "patient_name": {"type": "string", "required": True},
            "patient_address": {"type": "string", "required": False},
            "patient_dob": {"type": "date", "required": True},
            "patient_age": {"type": "integer", "required": True},
            "patient_sex": {"type": "string", "required": True},
            "prescription_date": {"type": "date", "required": True},
            "doctor_name": {"type": "string", "required": True},
            "doctor_title": {"type": "string", "required": True},
            "clinic_address": {"type": "string", "required": False},
            "clinic_phone": {"type": "string", "required": True},
            "medicine_name": {"type": "string", "required": True},
            "medicine_dose": {"type": "string", "required": True},
            "medicine_frequency": {"type": "string", "required": False},
            "medicine_duration": {"type": "string", "required": True},
            "instructions": {"type": "text", "required": True},
            "immunization": {"type": "string", "required": False},
            "immunization_date": {"type": "date", "required": False},
            "is_allergic": {"type": "boolean", "required": False},
            "weight": {"type": "string", "required": False},
            "is_pregnant": {"type": "boolean", "required": False}
        }
    
    def _mistral_structured_extraction(self, ocr_text: str) -> Dict[str, Any]:
        """Use Mistral with structured prompting for field extraction"""
        try:
            prompt = f"""
            Extract prescription information from the following OCR text and return it as a JSON object with these exact fields:
            
            Required fields to extract:
            - patient_name: Full name of the patient
            - patient_address: Patient's address (if mentioned)
            - patient_dob: Date of birth in DD/MM/YYYY format
            - patient_age: Age in years (number only)
            - patient_sex: Gender (Male/Female/M/F)
            - prescription_date: Date prescription was written
            - doctor_name: Doctor's full name
            - doctor_title: Doctor's title/degree (MD, DR, etc.)
            - clinic_address: Clinic or hospital address
            - clinic_phone: Clinic phone number
            - medicine_name: Name of prescribed medicines
            - medicine_dose: Dosage amounts and units
            - medicine_frequency: How often to take (daily, twice daily, etc.)
            - medicine_duration: How long to take the medicine
            - instructions: Special instructions or directions
            - immunization: Vaccine name (if any)
            - immunization_date: Vaccine date (if any)
            - is_allergic: true/false if allergies mentioned
            - weight: Patient weight with unit
            - is_pregnant: true/false if pregnancy mentioned
            
            OCR Text:
            {ocr_text}
            
            Return only valid JSON. If a field is not found, use empty string "" for text fields, null for boolean fields, and null for numbers.
            """
            
            # Use Mistral's chat completion for structured extraction
            response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            print(f"Mistral structured extraction error: {e}")
            return {}
    
    def _langchain_extraction(self, ocr_text: str) -> Dict[str, Any]:
        """Use LangChain with structured output parsing"""
        if not LANGCHAIN_AVAILABLE or not self.openai_api_key:
            return {}
        
        try:
            # Set up the parser
            parser = PydanticOutputParser(pydantic_object=PrescriptionData)
            
            # Create prompt template
            prompt = PromptTemplate(
                template="""Extract prescription information from the following text.
                {format_instructions}
                
                Text: {text}
                """,
                input_variables=["text"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Initialize OpenAI LLM
            llm = OpenAI(temperature=0, openai_api_key=self.openai_api_key)
            
            # Create the chain
            _input = prompt.format_prompt(text=ocr_text)
            output = llm(_input.to_string())
            
            # Parse the output
            parsed_output = parser.parse(output)
            return parsed_output.dict()
            
        except Exception as e:
            print(f"LangChain extraction error: {e}")
            return {}
    
    def _nlp_extraction(self, ocr_text: str) -> Dict[str, Any]:
        """Use SpaCy NLP for named entity recognition and pattern matching"""
        if not SPACY_AVAILABLE:
            return {}
        
        try:
            doc = self.nlp(ocr_text)
            extracted = {}
            
            # Extract persons (potential patient/doctor names)
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                # First person might be patient, last might be doctor
                extracted["patient_name"] = persons[0] if len(persons) > 0 else ""
                extracted["doctor_name"] = persons[-1] if len(persons) > 1 else ""
            
            # Extract dates
            dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            if dates:
                extracted["prescription_date"] = dates[0]
            
            # Extract organizations (potential clinics)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                extracted["clinic_address"] = orgs[0]
            
            # Extract numbers for age, doses, etc.
            numbers = [ent.text for ent in doc.ents if ent.label_ in ["CARDINAL", "QUANTITY"]]
            
            # Look for age patterns
            age_pattern = re.search(r'(\d{1,3})\s*(?:years?\s*old|y\.?o\.?|age)', ocr_text, re.IGNORECASE)
            if age_pattern:
                extracted["patient_age"] = int(age_pattern.group(1))
            
            # Look for gender
            gender_match = re.search(r'\b(male|female|m|f)\b', ocr_text, re.IGNORECASE)
            if gender_match:
                gender = gender_match.group(1).upper()
                extracted["patient_sex"] = "Male" if gender in ["MALE", "M"] else "Female"
            
            return extracted
            
        except Exception as e:
            print(f"NLP extraction error: {e}")
            return {}
    
    def _enhanced_regex_extraction(self, ocr_text: str) -> Dict[str, Any]:
        """Enhanced regex extraction with better patterns"""
        extracted = {}
        text = ocr_text.strip()
        
        # Enhanced patient name patterns
        name_patterns = [
            r'(?:FOR|Patient:?|Name:?)\s*(?:\([^)]*\))?\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)(?:\s*,\s*(?:HM\d+|USN|USNR))?',
            r'Patient\s*Name[:\-\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = re.sub(r',\s*(?:HM\d+|USN|USNR|MD|DR\.?).*?$', '', match.group(1), flags=re.IGNORECASE)
                extracted["patient_name"] = name.strip()
                break
        
        # Enhanced date patterns
        date_patterns = [
            r'(?:DATE|Prescription\s*Date)[:\-\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(?:DATE|Prescription\s*Date)[:\-\s]*(\d{1,2}\s+\w{3,9}\s+\d{2,4})',
            r'(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["prescription_date"] = match.group(1).strip()
                break
        
        # Enhanced doctor extraction
        doctor_patterns = [
            r'(?:Dr\.?\s+|Doctor\s+)?([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\s*,?\s*((?:MD|DR|LODR|USNR|DDS|DO|NP|PA)[\w\s\.]*)',
            r'SIGNATURE[:\-\s]*([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)\s*([\w\s\.]*(?:MD|DR|LODR)[\w\s\.]*)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["doctor_name"] = match.group(1).strip()
                if len(match.groups()) > 1 and match.group(2):
                    extracted["doctor_title"] = match.group(2).strip()
                break
        
        # Enhanced medicine extraction
        medicine_patterns = [
            r'(?:Tr|Rx)\s+([A-Za-z]+)\s+(\d+\s*(?:ml|mg|g|tablets?))',
            r'([A-Za-z]+)\s+(\d+\s*(?:ml|mg|g|tablets?))',
            r'Medicine[:\-\s]*([A-Za-z\s,]+)'
        ]
        
        medicines = []
        doses = []
        
        for pattern in medicine_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    med_name = match.group(1).strip()
                    if med_name.lower() not in ['and', 'or', 'with', 'the', 'a', 'an']:
                        medicines.append(med_name)
                        doses.append(match.group(2).strip())
        
        if medicines:
            extracted["medicine_name"] = ", ".join(medicines)
            extracted["medicine_dose"] = ", ".join(doses)
        
        # Enhanced instruction extraction
        instruction_patterns = [
            r'(?:Instructions?|Directions?|Sig|Signa)[:\-\s]*([^|\n]+)',
            r'(?:Take|Use)[:\-\s]*([^|\n]+)',
            r'Seg[:\-\s]*([^|\n]+)'
        ]
        
        for pattern in instruction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                instructions = match.group(1).strip()
                # Clean up common OCR artifacts
                instructions = re.sub(r'\s+', ' ', instructions)
                extracted["instructions"] = instructions
                break
        
        # Age extraction with better patterns
        age_patterns = [
            r'(?:Age|age)[:\-\s]*(\d{1,3})',
            r'(\d{1,3})\s*(?:years?\s*old|y\.?o\.?)',
            r'(?:under|age)\s*(\d{1,3})'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 < age < 120:  # Reasonable age range
                    extracted["patient_age"] = age
                break
        
        # Gender extraction
        gender_patterns = [
            r'(?:Sex|Gender)[:\-\s]*(Male|Female|M|F)\b',
            r'\b(Male|Female)\b',
            r'\b([MF])\b(?:\s|$)'
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).upper()
                if gender in ['M', 'MALE']:
                    extracted["patient_sex"] = "Male"
                elif gender in ['F', 'FEMALE']:
                    extracted["patient_sex"] = "Female"
                break
        
        # Clinic/facility extraction
        facility_patterns = [
            r'(?:MEDICAL\s+FACILITY|Clinic|Hospital)[:\-\s]*([^|\n]+?)(?=DATE|$)',
            r'(?:Address|Location)[:\-\s]*([^|\n]+)',
            r'U\.S\.S\.?\s*([^|\n]+)'
        ]
        
        for pattern in facility_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["clinic_address"] = match.group(1).strip()
                break
        
        return extracted
    
    def merge_extraction_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple extraction methods with confidence scoring"""
        merged = {}
        
        for field in self.schema.keys():
            field_values = []
            
            # Collect all non-empty values for this field
            for result in results:
                if field in result and result[field] and str(result[field]).strip():
                    field_values.append(result[field])
            
            if field_values:
                # For now, take the first non-empty value
                # TODO: Implement confidence scoring and voting
                merged[field] = field_values[0]
            else:
                # Set default values
                if self.schema[field]["type"] == "boolean":
                    merged[field] = None
                elif self.schema[field]["type"] == "integer":
                    merged[field] = None
                else:
                    merged[field] = ""
        
        return merged
    
    def extract_all_fields(self, ocr_text: str) -> Dict[str, Any]:
        """Extract fields using all available methods and merge results"""
        print(f"Using {len(self.extraction_methods)} extraction methods...")
        
        results = []
        
        # Run all extraction methods
        for i, method in enumerate(self.extraction_methods):
            try:
                print(f"Running extraction method {i+1}/{len(self.extraction_methods)}...")
                result = method(ocr_text)
                if result:
                    results.append(result)
                    print(f"Method {i+1} extracted {len([v for v in result.values() if v])} fields")
            except Exception as e:
                print(f"Extraction method {i+1} failed: {e}")
        
        # Merge results
        merged_result = self.merge_extraction_results(results)
        
        print(f"Final merged result has {len([v for v in merged_result.values() if v])} populated fields")
        
        return merged_result

def create_advanced_extractor(mistral_api_key: str, openai_api_key: Optional[str] = None) -> AdvancedPrescriptionExtractor:
    """Factory function to create advanced extractor"""
    return AdvancedPrescriptionExtractor(mistral_api_key, openai_api_key)

# Test function
def test_advanced_extraction():
    """Test the advanced extraction with sample data"""
    try:
        with open("ocr_result.txt", "r", encoding="utf-8") as f:
            ocr_text = f.read()
        
        # You can add your OpenAI API key here for additional extraction power
        openai_key = os.getenv('OPENAI_API_KEY')  # Set this environment variable
        mistral_key = os.getenv('MISTRAL_API_KEY')
        
        if not mistral_key:
            print("Please set MISTRAL_API_KEY environment variable")
            return
        
        extractor = create_advanced_extractor(mistral_key, openai_key)
        result = extractor.extract_all_fields(ocr_text)
        
        print("="*80)
        print("ADVANCED EXTRACTION RESULTS")
        print("="*80)
        
        for field, value in result.items():
            status = "✅" if value else "❌"
            print(f"{status} {field}: {value}")
        
        # Save results
        with open("advanced_extraction_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: advanced_extraction_result.json")
        
    except FileNotFoundError:
        print("OCR result file not found. Please run OCR extraction first.")

if __name__ == "__main__":
    test_advanced_extraction()