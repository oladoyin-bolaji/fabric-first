import streamlit as st
import ollama
from PIL import Image
import io
import re
import os
import matplotlib.pyplot as plt
import numpy as np

# UI configurations
st.set_page_config(page_title="Fabric First",
                   page_icon="👕🌿",
                   layout="wide")
st.image("images/header.jpg",caption=None,use_container_width=True,output_format="auto")
st.markdown("<h1 style='color:#FF69B4;'>FABRIC FIRST</h1>", unsafe_allow_html=True)

# Add CSS for material cards
st.markdown("""
<style>
.material-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    padding: 10px;
    margin-bottom: 20px;
    text-align: center;
    background-color: #f9f9f9;
    height: 100%;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("*Welcome to Fabric First!*")
    st.markdown("""        
    > This project helps you discover the **sustainability** and **durability** of your clothing, just by analyzing the label . 

    > Using cutting-edge AI, we provide insights into material composition, environmental impact, and whether this piece is a smart **investment** for your wardrobe !
    """)

    st.divider()
    st.subheader("🔍 What You'll Get:")
    st.write("""
    **Investment Value:** Find out if this item is a timeless treasure or a fast fashion faux pas . 
    This score is based on:
        
    1. **Sustainability Score :** How kind is this material to our planet?
    2. **Durability Score :** How long will this this last in your closet?
    """)
    st.divider()
    st.subheader("🧵 Material Breakdown")
    st.write("Get detailed insights into the materials that make up your clothing, including their quality and environmental impact ")

    st.divider()
    st.write("[Check out my GitHub for this project! 👩🏿‍💻](https://github.com/oladoyin-bolaji/fabric-first/tree/main)")

# Streamlit app title
st.info("**Make Informed Clothing Investments with AI-Generated Fabric Insights**", icon="👕")
st.divider()

# Camera and file upload options
st.write("Take a picture or upload an image of the material composition clothing label - typically found on the inside the garment")
camera_tab, upload_tab = st.tabs(["📸 Camera", "📤 Upload"])

picture = None

# Camera tab
with camera_tab:
    try:
        enable_camera = st.checkbox("Allow camera permissions")
        if enable_camera:
            camera_picture = st.camera_input("Take a photo")
            if camera_picture:
                picture = camera_picture
            else:
                st.info("Please allow the camera access in your browser settings.")
        else:
            st.info("Enable camera access to take a photo.")
    except Exception as e:
        st.error(f"Camera error: {str(e)}")
        st.info("Please use the Upload tab instead")

# File Upload
with upload_tab:
    uploaded_picture = st.file_uploader("Upload a photo of the clothing label", type=["jpg", "jpeg", "png"])
    if uploaded_picture:
        picture = uploaded_picture
        st.image(picture)

# Processing
if picture:
    try:
        img = Image.open(io.BytesIO(picture.getvalue()))
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # Try extracting text using Ollama
        try:
            with st.spinner("Analysing Materials"):
                response = ollama.chat(
                    model="llama3.2-vision",
                    messages=[{
                        "role": "user",
                        "content": "Extract the text from this image and the material composition of the clothing item",
                        "images": [img_bytes]
                    }]
                )
                extracted_text = response.get("message", {}).get("content", "").strip()

                if not extracted_text:
                    raise ValueError("Ollama failed to extract text")

        except Exception as e:
            st.warning(f"Ollama failed: {e}")

    except Exception as e:
        st.error(f"Error processing the image: {str(e)}")

    # Proceed with analysis if text was extracted
    if extracted_text:
        summary_response = ollama.chat(
            model="llama3.2-vision",
            messages=[{
                "role": "user",
                "content": f"""
Analyze the material composition of the garments in: {extracted_text}.  

1. **Generate three scores (each out of 10) based on:**  
   - **Environmental Sustainability** (impact of materials on the environment).  
   - **Durability** (how long the material is expected to last).  
   - **Material Quality** (overall quality and feel of the fabric).  

2. **Display each score in a structured format.**

3. **List all the specific fabrics/materials mentioned in the label (e.g., cotton, polyester, wool, etc.).**
"""
            }]
        )
        summary_text = summary_response.get("message", {}).get("content", "No summary available.")
        
        # Extract identified materials using another query
        materials_response = ollama.chat(
            model="llama3.2-vision",
            messages=[{
                "role": "user",
                "content": f"""
Based on the text '{extracted_text}', identify ONLY the specific fabric materials present in this clothing item.
Return the result as a comma-separated list of material names only (e.g., "Cotton, Polyester, Elastane").
Do not include percentages, just the material names.
"""
            }]
        )
        identified_materials = materials_response.get("message", {}).get("content", "").strip()
        identified_materials_list = [m.strip() for m in identified_materials.split(',')]

        # Extract scores 
        scores = re.findall(r"(\d+)/10", summary_text)

        if len(scores) >= 3:
            sustainability_score = int(scores[0])
            durability_score = int(scores[1])
            quality_score = int(scores[2])
            
            # Calculate Investment Value Score
            investment_value = (sustainability_score + durability_score) / 2 * 10 
            st.divider()
            
            st.subheader("Investment Value")
            st.metric("Investment Value Rating", f"{investment_value:.1f}%")

            # Pie charts for sustainability and durability scores
            col1, col2 = st.columns(2)
            
            with col1:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie([sustainability_score, 10-sustainability_score], 
                       labels=[f"Score: {sustainability_score}/10", ""], 
                       colors=['#2E86C1', '#E5E8E8'],
                       startangle=90,
                       wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                ax.set_title('Environmental Sustainability Score')
                ax.axis('equal')
                st.pyplot(fig)
            
            with col2:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie([durability_score, 10-durability_score], 
                       labels=[f"Score: {durability_score}/10", ""], 
                       colors=['#27AE60', '#E5E8E8'],
                       startangle=90,
                       wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                ax.set_title('Material Durability Score')
                ax.axis('equal')
                st.pyplot(fig)

        else:
            st.warning("Failed to extract all three scores from the summary.")
    
    st.divider()
