import streamlit as st
import ollama
from PIL import Image
import io
import pytesseract
import re
import os
import matplotlib.pyplot as plt
import numpy as np

# UI configurations
st.set_page_config(page_title="Fabric First",
                   page_icon="👕🌿",
                   layout="wide")
st.image("images/header.jpg",caption=None,use_container_width=True,output_format="auto")
# st.markdown("# :blue[FABRIC FIRST]")
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
    # Add a brief description of the project
    st.subheader("*Welcome to Fabric First!*")
    st.markdown("""        
    > This project helps you discover the **sustainability** and **durability** of your clothing, just by analyzing the label . 

    > Using cutting-edge AI, we provide insights into material composition, environmental impact, and whether this piece is a smart **investment** for your wardrobe !
    """)

    st.divider()
    # Add a section on what results will be generated
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
    # Add a link to your GitHub profile or project repository
    st.write("[Check out my GitHub for more about this project 👩🏿‍💻](https://github.com/oladoyin-bolaji/fabric-first/tree/main)")

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
        # Asking for camera permissions
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
                    raise ValueError("Ollama failed to extract text, using OCR fallback...")

        except Exception as e:
            st.warning(f"Ollama failed: {e}")
            extracted_text = pytesseract.image_to_string(img).strip()


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
            
            # Calculate Investment Value Score (average of sustainability and durability)
            investment_value = (sustainability_score + durability_score) / 2 * 10  # Convert to percentage
            st.divider()
            
            # Investment Value Score section
            st.subheader("Investment Value")
            st.metric("Investment Value Rating", f"{investment_value:.1f}%")
            
            # Pie charts for sustainability and durability scores
            col1, col2 = st.columns(2)
            
            with col1:
                # Sustainability score pie chart
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
                # Durability score pie chart
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie([durability_score, 10-durability_score], 
                       labels=[f"Score: {durability_score}/10", ""], 
                       colors=['#27AE60', '#E5E8E8'],
                       startangle=90,
                       wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                ax.set_title('Material Durability Score')
                ax.axis('equal')
                st.pyplot(fig)

            # Generate explanation for the scores and recommendation
            with st.spinner("Generating analysis..."):
                explanation_response = ollama.chat(
                    model="llama3.2-vision",
                    messages=[{
                        "role": "user",
                        "content": f"""
Based on the extracted material composition from '{extracted_text}', the item received:
- Environmental Sustainability score: {sustainability_score}/10
- Material Durability score: {durability_score}/10
- Overall Investment Value: {investment_value:.1f}%

First, explain why these scores were given, specifically addressing the environmental impact and durability aspects of the materials identified.
Then, make a clear recommendation on whether this item is a good investment piece or if it's fast fashion.
Keep your response concise but informative.
"""
                    }]
                )
                explanation_text = explanation_response.get("message", {}).get("content", "No explanation available.")
                
                st.subheader("Analysis & Recommendation:")
                st.write(explanation_text)

            # Material Breakdown - only for identified materials
            st.subheader("The Fabric Breakdown")
            
            # Dictionary of materials
            materials = {
                "Cotton": {
                    "description": "Cotton is one of the most widely used natural fibers, prized for its softness, breathability, and comfort. It's a renewable fiber that is highly absorbent, making it a popular choice for casual wear. Cotton fabrics are generally durable and easy to care for but may shrink after washing.",
                    "image_path": "images/cotton.jpg"
                },
                "Polyester": {
                    "description": "Polyester is a synthetic fiber known for its strength, durability, and resistance to shrinking or stretching. While not as breathable as natural fibers, it's often used in a blend to enhance wrinkle resistance and retain shape. Polyester is also quick-drying and can be made from recycled plastic bottles, making it a more eco-friendly option.",
                    "image_path": "images/polyester.jpg"
                },
                "Wool": {
                    "description": "Wool is a natural fiber derived from the fleece of sheep. It's highly valued for its insulating properties, providing warmth even when wet. Wool is also naturally moisture-wicking and resists wrinkles. It's a great option for colder climates, but it can be heavy and may require careful cleaning to avoid shrinking.",
                    "image_path": "images/wool.jpg"
                },
                "Silk": {
                    "description": "Silk is a luxurious natural fiber produced by silkworms. Known for its smooth texture, luster, and natural sheen, silk is often used in high-end fashion. It is lightweight, breathable, and comfortable, though it is prone to damage from sunlight, abrasion, and perspiration. Proper care is needed to maintain its beauty.",
                    "image_path": "images/silk.jpg"
                },
                "Linen": {
                    "description": "Linen is a lightweight, breathable fabric made from the flax plant. It is naturally cooling, making it ideal for warm climates, and is more absorbent than cotton. However, linen tends to wrinkle easily, which may be a concern for some wearers. Despite this, its natural texture and crisp appearance make it a popular choice for summer clothing.",
                    "image_path": "images/linen.jpg"
                },
                "Leather": {
                    "description": "Leather is a durable material made from animal hides, commonly used for outerwear, shoes, bags, and accessories. It's tough, flexible, and ages beautifully, developing a unique patina over time. Leather is water-resistant but requires regular maintenance to prevent cracking and to keep it supple.",
                    "image_path": "images/leather.jpg"
                },
                "Nylon": {
                    "description": "Nylon is a synthetic fiber known for its strength, elasticity, and resistance to moisture. It is commonly used in activewear, outerwear, and bags due to its durability and water-resistant properties. However, it is less breathable than natural fibers and is often blended with other materials to improve comfort.",
                    "image_path": "images/nylon.jpg"
                },
                "Acrylic": {
                    "description": "Acrylic is a lightweight, soft, and synthetic fiber that is often used as an alternative to wool. It retains its color and shape well and is resistant to fading. Acrylic fabrics are known for being warm and lightweight, but they can sometimes be less breathable than natural fibers, and their texture can feel synthetic to some users.",
                    "image_path": "images/acrylic.jpg"
                },
                "Rayon": {
                    "description": "Rayon is a semi-synthetic fiber made from regenerated cellulose, often from wood pulp. It is known for its soft, smooth texture and drape, making it ideal for flowing garments. Rayon is breathable and absorbent but can be prone to wrinkles and may require dry cleaning to preserve its shape.",
                    "image_path": "images/rayon.jpg"
                },
                "Spandex": {
                    "description": "Spandex, also known as Lycra or elastane, is a highly elastic synthetic fiber used in activewear, swimwear, and performance costumes. It stretches up to five times its original length, making it ideal for form-fitting clothing. Spandex is durable and resistant to fading but may lose its elasticity over time with improper care.",
                    "image_path": "images/spandex.jpg"
                },
                "Elastane": {
                    "description": "Elastane (also known as spandex or Lycra) is a synthetic fiber known for its exceptional elasticity. It can stretch to 5-8 times its original length and recover its shape when released. Commonly used in small percentages (2-10%) in clothing to provide stretch and improve fit, elastane enhances comfort and movement while maintaining garment shape.",
                    "image_path": "images/spandex.jpg"  # Using spandex image since they're the same
                },
                "Viscose": {
                    "description": "Viscose is a semi-synthetic fiber made from wood pulp that's been chemically processed. It's known for its silk-like feel, breathability, and excellent drape. Viscose fabrics are soft, lightweight, and absorbent, making them comfortable in warm weather. However, they can shrink when washed and may require special care.",
                    "image_path": "images/rayon.jpg"  # Using rayon image since they're similar
                }
            }

            # Filter materials to only show those identified in the clothing
            filtered_materials = {}
            for material in identified_materials_list:
                material = material.strip().capitalize()  # Normalize material names
                if material in materials:
                    filtered_materials[material] = materials[material]
                    
            if not filtered_materials:
                st.write("No specific materials could be identified from the label.")
            else:
                # Create a grid layout
                cols_per_row = 3
                materials_list = list(filtered_materials.items())

                # Create rows of materials
                for i in range(0, len(materials_list), cols_per_row):
                    # Create columns for this row
                    cols = st.columns(cols_per_row)
                    
                    # Fill each column with a material card
                    for col_idx in range(cols_per_row):
                        # Check if we still have materials to display
                        material_idx = i + col_idx
                        if material_idx < len(materials_list):
                            material, data = materials_list[material_idx]
                            
                            with cols[col_idx]:
                                # Display image (already sized correctly)
                                if os.path.exists(data["image_path"]):
                                    st.image(data["image_path"], caption=material)
                                else:
                                    st.warning(f"Image for {material} not found")
                                
                                # Add description below the image
                                st.write(data["description"])

        else:
            st.warning("Failed to extract all three scores from the summary.")
    
    st.divider()
