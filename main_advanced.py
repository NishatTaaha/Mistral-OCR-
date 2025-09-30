import streamlit as st
import os
import base64
import json
import time
from mistralai import Mistral

# Import the advanced extractor
try:
    from advanced_prescription_extractor import create_advanced_extractor
    ADVANCED_EXTRACTOR_AVAILABLE = True
except ImportError:
    ADVANCED_EXTRACTOR_AVAILABLE = False
    st.error("Advanced extractor not available. Please install required dependencies.")

st.set_page_config(layout="wide", page_title="Advanced Mistral OCR", page_icon="🏥")
st.title("🏥 Advanced Mistral OCR - Multi-Method Field Extraction")
st.markdown("*Using AI-powered extraction with Mistral, LangChain, and NLP*")

# API Keys Input
col1, col2 = st.columns(2)
with col1:
    mistral_api_key = st.text_input("Enter your Mistral API Key", type="password")
with col2:
    openai_api_key = st.text_input("Enter OpenAI API Key (Optional)", type="password", help="For enhanced LangChain extraction")

if not mistral_api_key:
    st.info("Please enter your Mistral API key to continue.")
    st.stop()

# Initialize session state variables for persistence
if "ocr_result" not in st.session_state:
    st.session_state["ocr_result"] = []
if "structured_data" not in st.session_state:
    st.session_state["structured_data"] = []
if "preview_src" not in st.session_state:
    st.session_state["preview_src"] = []
if "image_bytes" not in st.session_state:
    st.session_state["image_bytes"] = []

# Extraction method selection
st.sidebar.header("🔧 Extraction Settings")
use_advanced = st.sidebar.checkbox("Use Advanced Multi-Method Extraction", value=True, 
                                 help="Combines multiple AI techniques for better accuracy")

if use_advanced:
    st.sidebar.info("📊 Active Methods:\n- Mistral Structured Prompting\n- Enhanced Regex Patterns\n" + 
                   ("- LangChain with OpenAI\n" if openai_api_key else "") +
                   ("- SpaCy NLP Analysis\n" if False else ""))  # SpaCy temporarily disabled

# File type and source selection
col1, col2 = st.columns(2)
with col1:
    file_type = st.radio("Select file type", ("PDF", "Image"))
with col2:
    source_type = st.radio("Select source type", ("URL", "Local Upload"))

input_url = ""
uploaded_files = []

if source_type == "URL":
    input_url = st.text_area("Enter one or multiple URLs (separate with new lines)")
else:
    uploaded_files = st.file_uploader("Upload one or more files", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)

# Process Button & OCR Handling
if st.button("🚀 Process with Advanced Extraction"):
    if source_type == "URL" and not input_url.strip():
        st.error("Please enter at least one valid URL.")
    elif source_type == "Local Upload" and not uploaded_files:
        st.error("Please upload at least one file.")
    else:
        client = Mistral(api_key=mistral_api_key)
        
        # Initialize advanced extractor if available
        if use_advanced and ADVANCED_EXTRACTOR_AVAILABLE:
            try:
                advanced_extractor = create_advanced_extractor(mistral_api_key, openai_api_key)
                st.success("✅ Advanced multi-method extractor initialized!")
            except Exception as e:
                st.warning(f"⚠️ Advanced extractor initialization failed: {e}. Using basic extraction.")
                advanced_extractor = None
        else:
            advanced_extractor = None
        
        # Clear previous results
        st.session_state["ocr_result"] = []
        st.session_state["structured_data"] = []
        st.session_state["preview_src"] = []
        st.session_state["image_bytes"] = []
        
        sources = input_url.split("\n") if source_type == "URL" else uploaded_files
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, source in enumerate(sources):
            status_text.text(f"Processing file {idx + 1} of {len(sources)}...")
            progress_bar.progress((idx) / len(sources))
            
            # Prepare document for OCR
            if file_type == "PDF":
                if source_type == "URL":
                    document = {"type": "document_url", "document_url": source.strip()}
                    preview_src = source.strip()
                else:
                    file_bytes = source.read()
                    encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")
                    document = {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded_pdf}"}
                    preview_src = f"data:application/pdf;base64,{encoded_pdf}"
            else:
                if source_type == "URL":
                    document = {"type": "image_url", "image_url": source.strip()}
                    preview_src = source.strip()
                else:
                    file_bytes = source.read()
                    mime_type = source.type
                    encoded_image = base64.b64encode(file_bytes).decode("utf-8")
                    document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_image}"}
                    preview_src = f"data:{mime_type};base64,{encoded_image}"
                    st.session_state["image_bytes"].append(file_bytes)
            
            try:
                # OCR Processing
                status_text.text(f"Extracting text from file {idx + 1}...")
                ocr_response = client.ocr.process(model="mistral-ocr-latest", document=document, include_image_base64=True)
                time.sleep(1)  # Rate limiting
                
                pages = ocr_response.pages if hasattr(ocr_response, "pages") else (ocr_response if isinstance(ocr_response, list) else [])
                raw_text = "\n\n".join(page.markdown for page in pages) or "No result found."
                
                # Advanced Field Extraction
                if advanced_extractor:
                    status_text.text(f"Running advanced extraction on file {idx + 1}...")
                    prescription_fields = advanced_extractor.extract_all_fields(raw_text)
                    
                    # Calculate completion metrics
                    total_fields = len(prescription_fields)
                    completed_fields = len([v for v in prescription_fields.values() if v and str(v).strip()])
                    required_fields = [
                        'patient_name', 'patient_age', 'patient_sex', 'prescription_date',
                        'doctor_name', 'doctor_title', 'medicine_name', 'medicine_dose',
                        'medicine_duration', 'instructions'
                    ]
                    required_completed = len([f for f in required_fields if prescription_fields.get(f)])
                    
                    structured_result = {
                        "prescription_data": prescription_fields,
                        "completion_status": {
                            "total_fields": total_fields,
                            "completed_fields": completed_fields,
                            "required_fields": len(required_fields),
                            "required_completed": required_completed,
                            "completion_percentage": (completed_fields / total_fields) * 100,
                            "required_completion_percentage": (required_completed / len(required_fields)) * 100
                        },
                        "extraction_method": "Advanced Multi-Method",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                else:
                    # Basic extraction fallback
                    structured_result = {
                        "prescription_data": {"raw_text": raw_text},
                        "completion_status": {"completion_percentage": 0, "required_completion_percentage": 0},
                        "extraction_method": "Basic OCR Only",
                        "error": "Advanced extraction not available"
                    }
                
            except Exception as e:
                raw_text = f"Error extracting result: {e}"
                structured_result = {
                    "prescription_data": {},
                    "completion_status": {"completion_percentage": 0, "required_completion_percentage": 0},
                    "extraction_method": "Error",
                    "error": str(e)
                }
            
            st.session_state["ocr_result"].append(raw_text)
            st.session_state["structured_data"].append(structured_result)
            st.session_state["preview_src"].append(preview_src)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Processing complete!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()

# Display Results
if st.session_state["ocr_result"]:
    for idx, (result, structured_data) in enumerate(zip(st.session_state["ocr_result"], st.session_state["structured_data"])):
        
        # File Header with improved metrics
        st.markdown("---")
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        
        with col_header1:
            st.markdown(f"### 📋 File {idx+1} Results")
            method = structured_data.get("extraction_method", "Unknown")
            st.caption(f"Method: {method}")
        
        with col_header2:
            if "completion_status" in structured_data:
                completion = structured_data["completion_status"]["completion_percentage"]
                st.metric("Overall", f"{completion:.1f}%")
        
        with col_header3:
            if "completion_status" in structured_data:
                required_completion = structured_data["completion_status"]["required_completion_percentage"]
                st.metric("Required", f"{required_completion:.1f}%")
        
        # Main Content Columns
        col1, col2 = st.columns([1, 1])
        
        # Left Column: Input Preview
        with col1:
            st.subheader(f"📄 Input {file_type} {idx+1}")
            if file_type == "PDF":
                pdf_embed_html = f'<iframe src="{st.session_state["preview_src"][idx]}" width="100%" height="500" frameborder="0"></iframe>'
                st.markdown(pdf_embed_html, unsafe_allow_html=True)
            else:
                if source_type == "Local Upload" and st.session_state["image_bytes"]:
                    st.image(st.session_state["image_bytes"][idx], use_column_width=True)
                else:
                    st.image(st.session_state["preview_src"][idx], use_column_width=True)
        
        # Right Column: Structured Results
        with col2:
            st.subheader(f"🎯 Extracted Fields {idx+1}")
            
            if "prescription_data" in structured_data and structured_data["prescription_data"]:
                prescription_fields = structured_data["prescription_data"]
                
                # Display fields with enhanced formatting
                # Patient Information
                with st.expander("👤 Patient Information", expanded=True):
                    st.markdown(f"**patient_name:** `{prescription_fields.get('patient_name', 'Not found')}`")
                    st.markdown(f"**patient_address:** `{prescription_fields.get('patient_address', 'Not found')}`")
                    st.markdown(f"**patient_dob:** `{prescription_fields.get('patient_dob', 'Not found')}`")
                    age_value = prescription_fields.get("patient_age", "")
                    st.markdown(f"**patient_age:** `{str(age_value) if age_value else 'Not found'}`")
                    st.markdown(f"**patient_sex:** `{prescription_fields.get('patient_sex', 'Not found')}`")
                    st.markdown(f"**weight:** `{prescription_fields.get('weight', 'Not found')}`")
                    
                    # Boolean fields with better display
                    allergy_status = prescription_fields.get("is_allergic")
                    if allergy_status is True:
                        st.markdown("**is_allergic:** `✅ Yes`")
                    elif allergy_status is False:
                        st.markdown("**is_allergic:** `❌ No`")
                    else:
                        st.markdown("**is_allergic:** `❔ Not found`")
                    
                    pregnancy_status = prescription_fields.get("is_pregnant")
                    if pregnancy_status is True:
                        st.markdown("**is_pregnant:** `✅ Yes`")
                    elif pregnancy_status is False:
                        st.markdown("**is_pregnant:** `❌ No`")
                    else:
                        st.markdown("**is_pregnant:** `❔ Not found`")
                
                # Doctor & Clinic Information
                with st.expander("🏥 Doctor & Clinic Information"):
                    st.markdown(f"**doctor_name:** `{prescription_fields.get('doctor_name', 'Not found')}`")
                    st.markdown(f"**doctor_title:** `{prescription_fields.get('doctor_title', 'Not found')}`")
                    st.markdown(f"**clinic_address:** `{prescription_fields.get('clinic_address', 'Not found')}`")
                    st.markdown(f"**clinic_phone:** `{prescription_fields.get('clinic_phone', 'Not found')}`")
                
                # Prescription Details
                with st.expander("💊 Prescription Details", expanded=True):
                    st.markdown(f"**prescription_date:** `{prescription_fields.get('prescription_date', 'Not found')}`")
                    st.markdown(f"**medicine_name:** `{prescription_fields.get('medicine_name', 'Not found')}`")
                    st.markdown(f"**medicine_dose:** `{prescription_fields.get('medicine_dose', 'Not found')}`")
                    st.markdown(f"**medicine_frequency:** `{prescription_fields.get('medicine_frequency', 'Not found')}`")
                    st.markdown(f"**medicine_duration:** `{prescription_fields.get('medicine_duration', 'Not found')}`")
                    
                    # Instructions with better formatting
                    instructions = prescription_fields.get('instructions', 'Not found')
                    if len(str(instructions)) > 100:
                        st.markdown("**instructions:**")
                        st.code(instructions, language=None)
                    else:
                        st.markdown(f"**instructions:** `{instructions}`")
                
                # Immunization Information
                with st.expander("💉 Immunization Information"):
                    st.markdown(f"**immunization:** `{prescription_fields.get('immunization', 'Not found')}`")
                    st.markdown(f"**immunization_date:** `{prescription_fields.get('immunization_date', 'Not found')}`")
            
            else:
                st.warning("No structured data available. Check extraction method or try different settings.")
                if "error" in structured_data:
                    st.error(f"Error: {structured_data['error']}")
            
            # Download Options with enhanced data
            st.subheader("📥 Download Results")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            # Enhanced download function
            def create_styled_download_link(data, filetype, filename, label, color="#ff6b6b"):
                if isinstance(data, dict):
                    data_str = json.dumps(data, ensure_ascii=False, indent=2)
                else:
                    data_str = str(data)
                
                b64 = base64.b64encode(data_str.encode()).decode()
                href = f'<a href="data:{filetype};base64,{b64}" download="{filename}" style="text-decoration: none; background-color: {color}; color: white; padding: 8px 12px; border-radius: 4px; font-size: 14px; margin: 2px;">{label}</a>'
                return href
            
            with col_d1:
                # Raw OCR JSON
                raw_json = {"raw_ocr_text": result, "timestamp": structured_data.get("timestamp")}
                link = create_styled_download_link(raw_json, "application/json", f"raw_ocr_{idx+1}.json", "📄 Raw OCR", "#4CAF50")
                st.markdown(link, unsafe_allow_html=True)
            
            with col_d2:
                # Structured Fields JSON
                if "prescription_data" in structured_data:
                    link = create_styled_download_link(structured_data["prescription_data"], "application/json", f"structured_{idx+1}.json", "🎯 Fields", "#2196F3")
                    st.markdown(link, unsafe_allow_html=True)
            
            with col_d3:
                # Complete Report JSON
                link = create_styled_download_link(structured_data, "application/json", f"complete_{idx+1}.json", "📊 Report", "#FF9800")
                st.markdown(link, unsafe_allow_html=True)

# Enhanced Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**💡 Pro Tips:**")
    st.markdown("- Use OpenAI API key for best extraction accuracy")
    st.markdown("- Upload clear, high-resolution images")
    st.markdown("- Multiple extraction methods provide better results")

with col2:
    st.markdown("**🔧 Extraction Methods:**")
    if use_advanced:
        st.markdown("✅ Mistral Structured Prompting")
        st.markdown("✅ Enhanced Regex Patterns") 
        st.markdown("✅ LangChain Integration" if openai_api_key else "⚠️ LangChain (No OpenAI Key)")
        st.markdown("⚠️ SpaCy NLP (Installing...)")
    else:
        st.markdown("🔧 Basic OCR Only")