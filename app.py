import os
import sys
import warnings
from io import BytesIO
from pypdf import PdfReader
from fpdf import FPDF

# 1. Silence background loop errors and environment warnings
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
from google import genai

# 2. Main Page Layout Optimization (Clean light theme setting)
st.set_page_config(
    page_title="ResumeAI - Professional Builder",
    page_icon="🚀",
    layout="wide"
)

# 3. Secure API Initialization
API_KEY = st.secrets.get("GEMINI_API_KEY")
try:
    if API_KEY:
        client = genai.Client(api_key=API_KEY)
    else:
        st.error("⚠️ Missing API Key. Configure GEMINI_API_KEY in your Streamlit Cloud Advanced Secrets panel.")
except Exception as e:
    st.error(f"API Initializer Error: {e}")

# --- IN-MEMORY PDF CREATION ENGINE ---
class CustomPDF(FPDF):
    def header(self):
        pass
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def build_pdf_file(resume_content):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Sanitizing common high-bit character encodings to avoid PDF generation errors
    safe_text = resume_content.encode('latin-1', 'replace').decode('latin-1')
    
    for line in safe_text.split('\n'):
        if line.strip().startswith('# '):
            pdf.ln(4)
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, line.replace('# ', '').strip(), ln=1)
            pdf.ln(2)
        elif line.strip().startswith('## '):
            pdf.ln(5)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 8, line.replace('## ', '').strip(), ln=1)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
            pdf.ln(2)
        else:
            pdf.set_font("Arial", size=10.5)
            pdf.multi_cell(0, 6, line, ln=1)
            
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- USER INTERFACE DESIGN ---

st.markdown(
    """
    <div style="background-color:#f8f9fa; padding:30px; border-radius:15px; text-align:center; border: 1px solid #e9ecef; margin-bottom: 25px;">
        <h1 style="color:#1e3a8a; font-size:42px; margin-bottom:10px;">🚀 Launch Your Career with ResumeAI</h1>
        <p style="color:#4b5563; font-size:18px; max-width:850px; margin:0 auto; line-height:1.6;">
            Transform your academic milestones, project logs, and raw text profiles into an elite, ATS-compliant developer resume. 100% Free. Built for BCA career readiness.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

col_left, col_right = st.columns([1.1, 1.2])

with col_left:
    st.markdown("### 📥 Profile Workspace Panel")
    
    # FEATURE: Optional base resume file reader
    uploaded_file = st.file_uploader("Upload existing resume (Optional PDF Parser)", type=["pdf"])
    parsed_text = ""
    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content:
                    parsed_text += text_content + "\n"
            st.success("🎉 Successfully read and extracted baseline text from your uploaded PDF!")
            with st.expander("Show Extracted File Text"):
                st.write(parsed_text)
        except Exception as f_err:
            st.error(f"File Parser Error: {f_err}")

    # Section A: Personal Identification
    st.markdown("#### 👤 1. Contact Information")
    name = st.text_input("Full Name", value="SHUBHASHIS PATRA")
    contact_info = st.text_input("Contact Details (Phone, Email, Location)", value="+919556495126 | subhasishpatra677@gmail.com | Berhampur, Odisha")
    social_links = st.text_input("Professional Profiles (GitHub / LinkedIn)", value="B4D4L-2005 | shubhashis-patra-bca2027")
    target_role = st.text_input("Target Career Track Position", value="AI Engineer / Software Developer")

    # Section B: Granular Academic Tracking
    st.markdown("#### 🎓 2. Education Details")
    edu_college = st.text_input("Institution / College Name", value="Imperial College, Berhampur")
    edu_degree = st.text_input("Degree Program", value="Bachelor of Computer Applications (BCA)")
    
    col_y1, col_y2 = st.columns(2)
    with col_y1:
        edu_start = st.text_input("Start Year", value="2024")
    with col_y2:
        edu_end = st.text_input("End Year / Expected Graduation", value="2027")
        
    edu_achievements = st.text_area("Academic Rankings, Scores, or Competition Awards", value="Top 10% of batch across all internal exams up to 3rd semester. Secured 3rd place in college coding competition.")

    # Section C: Professional Core Skills
    st.markdown("#### 🛠️ 3. Core Capabilities Inventory")
    skills_list = st.text_area("Technical Skills (Comma separated categories)", value="Python, Java, C, HTML/CSS/JS, MySQL, Oracle, MongoDB, Git/GitHub, VS Code, pandas, NumPy, Matplotlib, Seaborn")

    # Section D: Distinct Project Architecture Logs
    st.markdown("#### 💻 4. Technical Projects Portfolio")
    st.markdown("*Describe up to two key developer highlights below:*")
    
    p1_title = st.text_input("Project 1 Title", value="SkyBook Interface")
    p1_desc = st.text_area("Project 1 Focus Details", value="Designed interactive flight search/booking UI with real-time field validation and sanitization. Implemented responsive design frameworks using CSS Grid/Flexbox tested across 5+ physical test environments. Engineered dynamic date-picker components.")
    
    p2_title = st.text_input("Project 2 Title", value="DataETL Automation Pipeline")
    p2_desc = st.text_area("Project 2 Focus Details", value="Automated comprehensive ETL processes for 10K+ records via structured pandas cleaning routines. Constructed analytical charts using Matplotlib/Seaborn uncovering 5+ business insights. Realized 70% reduction in manual step latency.")

    # Section E: Credentials & Interests
    st.markdown("#### 🏅 5. Certifications & Background Interests")
    certs_list = st.text_area("Certificates & Focus Focus Fields", value="- Data Structures & Algorithms - Internshala (NSDC), Dec 2025\n- 30 Days Data Analytics using Python - Skill Course, Jan 2026\n- Focus Interests: Competitive Programming (LeetCode context), Automation Scripting")

    generate_btn = st.button("✨ Reconstruct and Standardize Resume Profile", type="primary")

with col_right:
    st.markdown("### 🖥️ Professional Live Preview Window")
    
    # Session state setup to hold the AI text output across downloads
    if "ai_resume_markdown" not in st.session_state:
        st.session_state.ai_resume_markdown = None

    if generate_btn:
        with st.spinner("AI Processing System analyzing structural parameters..."):
            try:
                # Engineering direct structural assembly instructions targeting your clean template rule
                prompt = f"""
                You are an elite corporate resume compiler. Rebuild the candidate profiles provided into an exceptional resume layout matching the schema parameters perfectly.
                
                TARGET PATHWAY: {target_role}
                
                CORE PROFILE METRICS:
                - Name: {name}
                - Contact: {contact_info}
                - Professional Links: {social_links}
                
                EDUCATION BOUNDS:
                - Institution: {edu_college}
                - Program: {edu_degree}
                - Timeline: {edu_start} - {edu_end}
                - Performance: {edu_achievements}
                
                CORE CAPABILITIES: {skills_list}
                
                PROJECT MATRIX:
                1. {p1_title}: {p1_desc}
                2. {p2_title}: {p2_desc}
                
                EXTRAS: {certs_list}
                
                EXTRACTED BASE RESUME TEXT (IF ANY AVAILABLE FROM PARSER):
                {parsed_text}
                
                STRUCTURAL LAYOUT COMPLIANCE RULES:
                Output your response completely inside standard text layout blocks following this clean schema layout rules. Do not print greetings or introductory fluff:
                
                # {name.upper()}
                {contact_info} | {social_links}
                
                ## Summary
                (Compile a powerful 3-sentence technical summary targeting a '{target_role}' role. Emphasize algorithmic problem solving and development proficiency.)
                
                ## Technical Projects
                * {p1_title}
                  - (Transform details into an action-oriented technical bullet using the STAR method)
                  - (Highlight UI engineering constraints or layout tests across devices)
                * {p2_title}
                  - (Transform details into an action-oriented technical bullet using the STAR method)
                  - (Highlight metrics-driven optimizations like 70% processing cuts or 10K+ records parsing)
                
                ## Education
                * {edu_college} — {edu_degree} ({edu_start} - {edu_end})
                  - Summary Focus: {edu_achievements}
                
                ## Technical Skills
                (Neatly organize structural language skills into inline category labels based on user data):
                **Languages:** (Categorized items)
                **Databases:** (Categorized items)
                **Tools & Libraries:** (Categorized items)
                
                ## Certifications & Professional Interests
                {certs_list}
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                st.session_state.ai_resume_markdown = response.text
                st.balloons()
                
            except Exception as ai_fault:
                st.error(f"Inference Engine Connection Fault: {ai_fault}")

    # Render workspace data if it has been compiled
    if st.session_state.ai_resume_markdown:
        st.success("🎉 Your Standardized Resume Layout is Ready!")
        
        # Action Block: Native PDF Downloader Tool
        with st.spinner("Compiling PDF bytes stream layout..."):
            pdf_data = build_pdf_file(st.session_state.ai_resume_markdown)
            
        st.download_button(
            label="📥 Download Your Clean Resume as PDF",
            data=pdf_data,
            file_name=f"{name.replace(' ', '_')}_Resume.pdf",
            mime="application/pdf",
            type="secondary"
        )
        
        st.write("---")
        
        # Display crisp layout card simulation matching the paper theme
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding:25px; border-radius:10px; border: 1px solid #ced4da; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: #000000; font-family: 'Courier New', Courier, monospace; white-space: pre-wrap;">
                {st.session_state.ai_resume_markdown}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("💡 Fill out or adjust your credentials on the left entry panel, upload an optional background PDF resume to scan, and click the layout reconstruction button to view your downloadable document preview here.")
