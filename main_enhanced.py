import streamlit as st
import os
import base64
import json
import time
from mistralai import Mistral
from prescription_field_extractor import PrescriptionFieldExtractor, process_prescription_image

st.set_page_config(layout="wide", page_title="Mistral OCR App - Enhanced", page_icon="🏥")
st.title("🏥 Mistral OCR App - Enhanced Field Extraction")
st.markdown("*Extract structured prescription data according to company schema*")

# 1. API Key Input
api_key = st.text_input("Enter your Mistral API Key", type="password")
if not api_key:
    st.info("Please enter your API key to continue.")
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

# 2. Choose file type: PDF or Image
file_type = st.radio("Select file type", ("PDF", "Image"))

# 3. Select source type: URL or Local Upload
source_type = st.radio("Select source type", ("URL", "Local Upload"))

input_url = ""
uploaded_files = []

if source_type == "URL":
    input_url = st.text_area("Enter one or multiple URLs (separate with new lines)")
else:
    uploaded_files = st.file_uploader("Upload one or more files", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)

# 4. Process Button & OCR Handling
if st.button("🔍 Process & Extract Fields"):
    if source_type == "URL" and not input_url.strip():
        st.error("Please enter at least one valid URL.")
    elif source_type == "Local Upload" and not uploaded_files:
        st.error("Please upload at least one file.")
    else:
        client = Mistral(api_key=api_key)
        extractor = PrescriptionFieldExtractor()
        
        # Clear previous results
        st.session_state["ocr_result"] = []
        st.session_state["structured_data"] = []
        st.session_state["preview_src"] = []
        st.session_state["image_bytes"] = []
        
        sources = input_url.split("\n") if source_type == "URL" else uploaded_files
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, source in enumerate(sources):
            status_text.text(f"Processing file {idx + 1} of {len(sources)}...")
            progress_bar.progress((idx) / len(sources))
            
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
                ocr_response = client.ocr.process(model="mistral-ocr-latest", document=document, include_image_base64=True)
                time.sleep(1)  # Rate limiting
                
                pages = ocr_response.pages if hasattr(ocr_response, "pages") else (ocr_response if isinstance(ocr_response, list) else [])
                raw_text = "\n\n".join(page.markdown for page in pages) or "No result found."
                
                # Enhanced Field Extraction
                structured_result = process_prescription_image(raw_text)
                
            except Exception as e:
                raw_text = f"Error extracting result: {e}"
                structured_result = {
                    "prescription_data": {},
                    "completion_status": {"completion_percentage": 0, "required_completion_percentage": 0},
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

# 5. Display Results
if st.session_state["ocr_result"]:
    for idx, (result, structured_data) in enumerate(zip(st.session_state["ocr_result"], st.session_state["structured_data"])):
        
        # File Header
        st.markdown("---")
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"### 📋 File {idx+1} Results")
        with col_header2:
            if "completion_status" in structured_data:
                completion = structured_data["completion_status"]["completion_percentage"]
                required_completion = structured_data["completion_status"]["required_completion_percentage"]
                st.metric("Completion", f"{completion:.1f}%", f"Required: {required_completion:.1f}%")
        
        # Main Content Columns
        col1, col2 = st.columns([1, 1])
        
        # Left Column: Input Preview
        with col1:
            st.subheader(f"📄 Input {file_type} {idx+1}")
            if file_type == "PDF":
                pdf_embed_html = f'<iframe src="{st.session_state["preview_src"][idx]}" width="100%" height="600" frameborder="0"></iframe>'
                st.markdown(pdf_embed_html, unsafe_allow_html=True)
            else:
                if source_type == "Local Upload" and st.session_state["image_bytes"]:
                    st.image(st.session_state["image_bytes"][idx], use_column_width=True)
                else:
                    st.image(st.session_state["preview_src"][idx], use_column_width=True)
        
        # Right Column: Structured Results
        with col2:
            st.subheader(f"🎯 Extracted Fields {idx+1}")
            
            if "prescription_data" in structured_data:
                prescription_fields = structured_data["prescription_data"]
                completion_status = structured_data.get("completion_status", {})
                
                # Display extracted fields in organized sections
                
                # Patient Information
                with st.expander("👤 Patient Information", expanded=True):
                    st.markdown(f"**patient_name:** `{prescription_fields.get('patient_name', 'Not found')}`")
                    st.markdown(f"**patient_address:** `{prescription_fields.get('patient_address', 'Not found')}`")
                    st.markdown(f"**patient_dob:** `{prescription_fields.get('patient_dob', 'Not found')}`")
                    age_value = prescription_fields.get("patient_age", "")
                    st.markdown(f"**patient_age:** `{str(age_value) if age_value else 'Not found'}`")
                    st.markdown(f"**patient_sex:** `{prescription_fields.get('patient_sex', 'Not found')}`")
                    st.markdown(f"**weight:** `{prescription_fields.get('weight', 'Not found')}`")
                    allergy_status = prescription_fields.get("is_allergic")
                    allergy_text = "Yes" if allergy_status is True else "No" if allergy_status is False else "Not found"
                    st.markdown(f"**is_allergic:** `{allergy_text}`")
                    pregnancy_status = prescription_fields.get("is_pregnant")
                    pregnancy_text = "Yes" if pregnancy_status is True else "No" if pregnancy_status is False else "Not found"
                    st.markdown(f"**is_pregnant:** `{pregnancy_text}`")
                
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
                    
                    # Instructions with line breaks for better readability
                    instructions = prescription_fields.get('instructions', 'Not found')
                    if len(instructions) > 100:
                        st.markdown(f"**instructions:**")
                        st.code(instructions, language=None)
                    else:
                        st.markdown(f"**instructions:** `{instructions}`")
                
                # Immunization Information
                with st.expander("💉 Immunization Information"):
                    st.markdown(f"**immunization:** `{prescription_fields.get('immunization', 'Not found')}`")
                    st.markdown(f"**immunization_date:** `{prescription_fields.get('immunization_date', 'Not found')}`")
            
            # Download Options
            st.subheader("📥 Download Results")
            
            # Create download data
            def create_download_link(data, filetype, filename, label):
                if isinstance(data, dict):
                    data_str = json.dumps(data, ensure_ascii=False, indent=2)
                else:
                    data_str = str(data)
                
                b64 = base64.b64encode(data_str.encode()).decode()
                href = f'<a href="data:{filetype};base64,{b64}" download="{filename}" style="text-decoration: none; background-color: #ff6b6b; color: white; padding: 8px 12px; border-radius: 4px; font-size: 14px;">{label}</a>'
                return href
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                # Raw OCR JSON
                raw_json = {"raw_ocr_text": result}
                link = create_download_link(raw_json, "application/json", f"raw_ocr_{idx+1}.json", "📄 Raw OCR")
                st.markdown(link, unsafe_allow_html=True)
            
            with col_d2:
                # Structured Fields JSON
                if "prescription_data" in structured_data:
                    link = create_download_link(structured_data["prescription_data"], "application/json", f"structured_fields_{idx+1}.json", "🎯 Structured")
                    st.markdown(link, unsafe_allow_html=True)
            
            with col_d3:
                # Complete Report JSON
                link = create_download_link(structured_data, "application/json", f"complete_report_{idx+1}.json", "📊 Complete")
                st.markdown(link, unsafe_allow_html=True)
            
            # Field Completion Status
            if "completion_status" in structured_data:
                st.subheader("📈 Field Completion Status")
                
                field_status = structured_data["completion_status"]["field_status"]
                
                # Show required vs optional completion
                required_fields = {k: v for k, v in field_status.items() if v["required"]}
                optional_fields = {k: v for k, v in field_status.items() if not v["required"]}
                
                col_req, col_opt = st.columns(2)
                
                with col_req:
                    st.markdown("**Required Fields:**")
                    for field_name, status in required_fields.items():
                        icon = "✅" if status["completed"] else "❌"
                        st.write(f"{icon} {field_name.replace('_', ' ').title()}")
                
                with col_opt:
                    st.markdown("**Optional Fields:**")
                    for field_name, status in optional_fields.items():
                        icon = "✅" if status["completed"] else "⚪"
                        st.write(f"{icon} {field_name.replace('_', ' ').title()}")

# Footer
st.markdown("---")
st.markdown("**💡 Tip:** This app extracts prescription fields according to your company's schema requirements. All critical fields (patient info, doctor info, medications) are prioritized for extraction.")