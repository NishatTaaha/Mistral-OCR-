#!/usr/bin/env python3
import base64
import os
from mistralai import Mistral

def extract_text_from_image(image_path, api_key):
    """
    Extract text from an image using Mistral OCR API
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None
    
    # Read and encode the image
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Determine MIME type based on file extension
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
        result_text = "\n\n".join(page.markdown for page in pages) or "No text found."
        
        return result_text
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def main():
    # Image path
    image_path = r"c:\ICEL_TECH_WORKSPACE\Mistral-OCR-\A-sample-prescription-image-in-grayscale-version.png"
    
    # Get API key from environment variable or user input
    api_key = os.getenv('MISTRAL_API_KEY')
    
    if not api_key:
        print("Please set your Mistral API key as an environment variable:")
        print("Set MISTRAL_API_KEY=your_api_key_here")
        print("\nOr enter it now:")
        api_key = input("Enter your Mistral API Key: ").strip()
        
    if not api_key:
        print("Error: No API key provided!")
        return
    
    # Extract text
    extracted_text = extract_text_from_image(image_path, api_key)
    
    if extracted_text:
        print("\n" + "="*60)
        print("EXTRACTED TEXT:")
        print("="*60)
        print(extracted_text)
        print("="*60)
        
        # Save to file
        output_file = "ocr_result.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        print(f"\nText saved to: {output_file}")
    else:
        print("Failed to extract text from image.")

if __name__ == "__main__":
    main()