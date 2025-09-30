# 🏥 Advanced Prescription OCR System

An advanced AI-powered OCR system for extracting structured data from prescription images and PDFs using Mistral AI, with multiple extraction methods for enhanced accuracy.

## 🚀 Features

### Multi-Method AI Extraction
- **Mistral Structured Prompting**: AI-powered field extraction with structured prompts
- **LangChain Integration**: Advanced language processing with OpenAI models
- **Enhanced Regex Patterns**: Improved pattern recognition for medical terminology
- **SpaCy NLP Analysis**: Named entity recognition and medical text understanding

### Supported Formats
- 📄 PDF prescriptions
- 🖼️ Image formats (PNG, JPG, JPEG)
- 🌐 URL-based file processing
- 📁 Local file uploads

### Field Extraction (CEO Schema Compliant)
Extracts **20 structured fields** according to company requirements:

#### Patient Information
- `patient_name` - Full name of the patient
- `patient_address` - Patient's address
- `patient_dob` - Date of birth
- `patient_age` - Age in years
- `patient_sex` - Gender (Male/Female)
- `weight` - Patient weight with unit
- `is_allergic` - Allergy status (boolean)
- `is_pregnant` - Pregnancy status (boolean)

#### Doctor & Clinic
- `doctor_name` - Prescribing doctor's name
- `doctor_title` - Medical title/degree
- `clinic_address` - Clinic or hospital address
- `clinic_phone` - Clinic phone number

#### Prescription Details
- `prescription_date` - Date prescription was written
- `medicine_name` - Prescribed medication names
- `medicine_dose` - Dosage amounts and units
- `medicine_frequency` - Dosing frequency
- `medicine_duration` - Treatment duration
- `instructions` - Special instructions

#### Immunization
- `immunization` - Vaccine name (if applicable)
- `immunization_date` - Vaccination date

## 🎯 Accuracy Improvements

| Method | Accuracy | Fields Extracted |
|--------|----------|------------------|
| **Basic Regex** | ~50% | 10/20 fields |
| **Advanced Multi-Method** | ~75%+ | 15+/20 fields |

### Sample Results Comparison

**Before (Basic):**
```
patient_name: John R. Doe ✅
medicine_name: Belledenna, Tr, Amphogel ⚠️
medicine_dose: 15 ml, Belledenna, gaad ⚠️
```

**After (Advanced):**
```
patient_name: John R. Doe ✅
patient_sex: Male ✅ (NEW!)
medicine_name: ['Tr Belledenna 15 ml', 'Amphogel gaad 120 ml'] ✅
medicine_dose: ['5 ml'] ✅ (ACCURATE!)
instructions: M & F1 Solution; Seg: 5ml lid a.c. ✅
```

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NishatTaaha/Advanced-Prescription-OCR.git
   cd Advanced-Prescription-OCR
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download SpaCy model (optional):**
   ```bash
   python -m spacy download en_core_web_sm
   ```

## 🔑 API Keys Setup

You'll need a Mistral AI API key. OpenAI key is optional but recommended for best accuracy.

### Environment Variables (Recommended)
```bash
export MISTRAL_API_KEY="your_mistral_api_key_here"
export OPENAI_API_KEY="your_openai_api_key_here"  # Optional
```

### Or enter in the app interface

## 🚀 Usage

### 1. Basic OCR App
```bash
streamlit run main.py
```
Access at: http://localhost:8501

### 2. Enhanced UI App
```bash
streamlit run main_enhanced.py --server.port 8502
```
Access at: http://localhost:8502

### 3. Advanced Multi-Method App (Recommended)
```bash
streamlit run main_advanced.py --server.port 8503
```
Access at: http://localhost:8503

### 4. Command Line Extraction
```bash
python advanced_prescription_extractor.py
```

## 📁 Project Structure

```
├── main.py                           # Basic OCR app
├── main_enhanced.py                  # Enhanced UI app
├── main_advanced.py                  # Advanced multi-method app
├── advanced_prescription_extractor.py # Core advanced extractor
├── prescription_field_extractor.py   # Basic field extractor
├── extract_image_text.py            # Simple text extraction
├── extract_prescription_fields.py   # Basic field extraction
├── requirements.txt                 # Python dependencies
├── data/                           # Sample prescription images (129 files)
├── README.md                       # This file
└── .gitignore                     # Git ignore rules
```

## 🛠️ Technical Architecture

### Core Components

1. **OCR Engine**: Mistral AI OCR API
2. **Field Extraction**: Multi-method AI approach
3. **UI Framework**: Streamlit
4. **Data Validation**: Pydantic models
5. **NLP Processing**: SpaCy (optional)

### Extraction Pipeline

```
Image/PDF → Mistral OCR → Multi-Method Extraction → Structured JSON → UI Display
                            ↓
            [Mistral Prompting, LangChain, Regex, NLP]
```

## 🎯 Use Cases

- 🏥 **Healthcare Systems**: Digitize paper prescriptions
- 📊 **Data Entry Automation**: Reduce manual prescription processing
- 🔍 **Medical Record Management**: Extract structured prescription data
- 🌍 **Multi-language Support**: Process prescriptions in various languages
- 📈 **Analytics**: Generate insights from prescription patterns

## 📊 Performance Metrics

- **Processing Speed**: ~2-5 seconds per prescription
- **Field Accuracy**: 75%+ with advanced methods
- **Format Support**: PDF, PNG, JPG, JPEG
- **Concurrent Processing**: Multiple files supported
- **API Rate Limiting**: Built-in 1-second delays

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Mistral AI** for the OCR API
- **Streamlit** for the web framework
- **LangChain** for AI workflow management
- **SpaCy** for NLP capabilities

## 📞 Contact

- **Developer**: Nishat Taaha
- **GitHub**: [@NishatTaaha](https://github.com/NishatTaaha)
- **Project**: [Advanced-Prescription-OCR](https://github.com/NishatTaaha/Advanced-Prescription-OCR)

---

⭐ **Star this repository if you find it useful!**
