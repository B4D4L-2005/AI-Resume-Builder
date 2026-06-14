import os
import sys
import warnings

# 1. Silence background library and environment warnings
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

import streamlit as st
from google import genai

# 2. Main Page Setup (Light theme layout optimization)
st.set_page_config(
    page_title="ResumeAI - Standardizing Job Readiness",
    page_icon="🚀",
    layout="wide"
)

# 3. Secure API Client Initialization
# Pulls your Gemini API Key safely from the hosting server environment variables
API_KEY = st.secrets.get("GEMINI_API_KEY")

try:
    if API_KEY:
        client = genai.Client(api_key=API_KEY)
    else:
        st.error("⚠️ Missing API Key configuration. Please assign GEMINI_API_KEY in your Streamlit Advanced Settings.")
except Exception as e:
    st.error(f"API Client Initializer Error: {e}")

# --- APP INTERFACE DESIGN ---

# Elegant Corporate Header
st.markdown(
    """
    <div style="background-color:#f8f9fa; padding:30px; border-radius:15px; text-align:center; border: 1px solid #e9ecef; margin-bottom: 25px;">
        <h1 style="color:#1e3a8a; font-size:42px; margin-bottom:10px;">🚀 Launch Your Career with ResumeAI</h1>
        <p style="color:#4b5563; font-size:18px; max-width:700px; margin:0 auto; line-height:1.6;">
            Transform your academic milestones and technical projects into an elite, ATS-compliant developer resume. 100% Free. Built for BCA career readiness.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Core Competency Feature Blocks
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown("### 📄 Professional Parsing\nAccepts profile parameters directly to organize raw education histories into neat corporate formats.")
with col_f2:
    st.markdown("### 🛠️ STAR Optimization\nTransforms everyday project outlines into action-verb, metrics-oriented technical achievements.")
with col_f3:
    st.markdown("### 🎯 Key Alignment\nDynamically formats technical language to support hyper-targeted roles like AI Engineers or Software Developers.")

st.write("---")

# Split Screen Architecture
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("### 📥 Profile Input Workspace")
    
    # Input field groups pre-loaded with your specific academic resume credentials
    name = st.text_input("Full Name", value="SHUBHASHIS PATRA")
    contact = st.text_input("Contact Details", value="+919556495126 | subhasishpatra677@gmail.com | Berhampur, Odisha")
    socials = st.text_input("Professional Profiles (GitHub / LinkedIn)", value="B4D4L-2005 | shubhashis-patra-bca2027")
    target_job = st.text_input("Target Career Track / Position", value="AI Engineer / Software Developer")
    
    skills = st.text_area(
        "Technical Skills Inventory", 
        value="Python, Java, C, HTML/CSS/JS, MySQL, Oracle, MongoDB, Git/GitHub, VS Code, pandas, NumPy, Matplotlib, Seaborn"
    )
    
    experience_or_projects = st.text_area(
        "Describe Your Technical Projects / Applications", 
        value="SkyBook Interface: Flight search UI with CSS Grid/Flexbox.\nDataETL Automation Pipeline: Automated ETL for 10K+ records using pandas, cleaning data, and creating Matplotlib/Seaborn dashboards with 70% manual reduction."
    )
    
    education_achievements = st.text_area(
        "Academic Milestones & Distinctions",
        value="Imperial College, Berhampur - BCA (2024-2027). Top 10% of batch across all internal exams. Secured 3rd place in college coding competition."
    )

    generate_btn = st.button("✨ Upgrade to Professional Resume Layout", type="primary")

with col_right:
    st.markdown("### 🖥️ Standardized Live Output Preview")
    
    if generate_btn:
        with st.spinner("Processing prompt token inference blocks..."):
            try:
                # Engineering explicit instruction logic matching your structured profile template
                prompt = f"""
                You are an enterprise technical resume architect. Reconstruct the user background values provided below into a pristine, high-impact candidate layout.
                
                TARGET SPECIFICATION: {target_job}
                INPUT METRICS:
                - Name: {name}
                - Location/Contact: {contact}
                - URLs: {socials}
                - Core Skills: {skills}
                - Base Projects: {experience_or_projects}
                - Base Education: {education_achievements}
                
                STRUCTURAL LAYOUT COMPLIANCE RULES:
                Render your final response completely in plain markdown matching this exact syntax blocks without adding extra conversational greeting lines:
                
                # {name.upper()}
                {contact} | {socials}
                
                ## Summary
                (Generate a premier 3-sentence summary highlighting foundational strength in data structures, language runtimes, and engineering focus objectives.)
                
                ## Technical Projects
                (Create separate bold headings for each project. Generate 3 impact-focused bullet steps using the STAR method highlighting precise optimizations.)
                
                ## Education
                (Display college name, degree title, timeline details, core modules, and academic rankings or coding awards as clean items.)
                
                ## Technical Skills
                **Languages:** (Categorized split based on inputs)
                **Databases:** (Categorized split based on inputs)
                **Tools & Libraries:** (Categorized split based on inputs)
                
                ## Certifications & Professional Interests
                (Provide technical upskilling records and development interests as neat bullet entries.)
                """
                
                # Executing standard generative client call with updated model identifier
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                st.balloons()
                # Emulates crisp paper formatting within standard browser UI
                st.markdown(
                    f"""
                    <div style="background-color:#ffffff; padding:25px; border-radius:10px; border: 1px solid #ced4da; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: #000000; font-family: 'Courier New', Courier, monospace;">
                        {response.text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            except Exception as ai_err:
                st.error(f"Inference Engine Processing Fault: {ai_err}")
    else:
        st.info("💡 Review your engineering input indicators on the left configuration column and press the generation trigger to watch your professional resume layout build here.")
