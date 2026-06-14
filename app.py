import os
import sys
import warnings
from io import BytesIO
from pypdf import PdfReader
from fpdf import FPDF

# 1. Intercept background platform network loops and warnings
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
from google import genai

# 2. Page Configuration (Enforced clean light theme)
st.set_page_config(
    page_title="ResumeAI - Professional Single-Page Builder",
    page_icon="🚀",
    layout="wide"
)

# 3. Secure API Initialization via Environment Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")
try:
    if API_KEY:
        client = genai.Client(api_key=API_KEY)
    else:
        st.error("⚠️ Configuration Secret Key Missing. Add GEMINI_API_KEY to your Streamlit Cloud settings panel.")
except Exception as e:
    st.error(f"API Handshake Error: {e}")

# --- STRICT SINGLE-PAGE PDF COMPILER ENGINE ---
class StrictSinglePagePDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

def compile_one_page_pdf(markdown_text):
    # Enforcing compressed padding geometries to guarantee single-page limits
    pdf = StrictSinglePagePDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=12, top=10, right=12)
    pdf.add_page()
    
    # Sanitize high-bit string encodings to prevent fpdf encoding crash
    clean_text = markdown_text.encode('latin-1', 'replace').decode('latin-1')
    
    lines = clean_text.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(1.5) # Compressed spacing
            continue
            
        if stripped.startswith('# '):
            pdf.set_font("Arial", "B", 15)
            pdf.cell(0, 7, stripped.replace('# ', '').strip(), ln=1, align="C")
        elif stripped.startswith('## '):
            pdf.ln(2)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 5, stripped.replace('## ', '').strip().upper(), ln=1)
            # Solid divider accent block
            pdf.line(12, pdf.get_y(), 198, pdf.get_y())
            pdf.ln(1)
        elif stripped.startswith('* ') or stripped.startswith('- '):
            pdf.set_font("Arial", "", 9.5)
            # Implement automatic bullet character indentation alignment
            bullet_text = stripped[2:].strip()
            pdf.cell(4, 4.5, chr(149), ln=0)
            pdf.multi_cell(0, 4.5, bullet_text)
        else:
            pdf.set_font("Arial", "", 9.5)
            if "|" in stripped:
                pdf.cell(0, 4.5, stripped, ln=1, align="C")
            else:
                pdf.multi_cell(0, 4.5, stripped)
                
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- INITIALIZE DYNAMIC MEMORY TRACKS ---
if "edu_count" not in st.session_state: st.session_state.edu_count = 1
if "job_count" not in st.session_state: st.session_state.job_count = 1
if "proj_count" not in st.session_state: st.session_state.proj_count = 1
if "cert_count" not in st.session_state: st.session_state.cert_count = 1
if "ai_output_cache" not in st.session_state: st.session_state.ai_output_cache = None

# --- HEADER INTERFACE ---
st.markdown(
    """
    <div style="background-color:#f8f9fa; padding:25px; border-radius:12px; text-align:center; border: 1px solid #e9ecef; margin-bottom: 20px;">
        <h1 style="color:#1e3a8a; font-size:38px; margin:0 0 5px 0;">🚀 ResumeAI Platform</h1>
        <p style="color:#4b5563; font-size:16px; margin:0;">
            Compile structural profiles into a single-page corporate developer resume template layout from scratch.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

col_workspace, col_viewport = st.columns([1.1, 1.2])

with col_workspace:
    st.markdown("### 📥 Profile Input Workspace")
    
    # 1. OPTIONAL EXISTING RESUME PARSER
    uploaded_file = st.file_uploader("Upload an existing resume file to scan data points (Optional)", type=["pdf"])
    parsed_resume_text = ""
    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content: parsed_resume_text += text_content + "\n"
            st.success("🎉 Read system variables from file. Match your forms below:")
            with st.expander("View Scanned Content Logs"):
                st.write(parsed_resume_text)
        except Exception as f_err:
            st.error(f"Inbound File Processing Fault: {f_err}")

    # 2. PERSONAL IDENTITY CONFIGURATION (BLANK ENFORCED)
    st.markdown("#### 👤 Personal & Identification Particulars")
    user_name = st.text_input("Full Name (Capital Letters)", value="")
    p_email = st.text_input("Email Address Address", value="")
    p_phone = st.text_input("Mobile Contact Number (With Country Code)", value="")
    p_loc = st.text_input("Current Location (City, State)", value="")
    p_git = st.text_input("GitHub Profile URL Link", value="")
    p_link = st.text_input("LinkedIn Network Profile URL", value="")
    target_role = st.text_input("Target Career Employment Position", value="")

    # 3. GRANULAR TIMELINE EDUCATION OPTIONS (10TH TO PRESENT)
    st.markdown("#### 🎓 Academic History Tracking (10th, 12th, Graduation, etc.)")
    edu_data = []
    for i in range(st.session_state.edu_count):
        st.markdown(f"*Institution Entry Tier #{i+1}*")
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            inst = st.text_input(f"School / University Name #{i+1}", key=f"edu_inst_{i}")
            deg = st.text_input(f"Degree / Standard Certificate #{i+1}", key=f"edu_deg_{i}", placeholder="e.g., 10th / 12th / BCA")
        with col_ed2:
            timeline = st.text_input(f"Timeline Years #{i+1}", key=f"edu_time_{i}", placeholder="e.g., 2022 - 2024")
            score = st.text_input(f"CGPA / Percentage Obtained #{i+1}", key=f"edu_score_{i}")
        edu_data.append({"institution": inst, "degree": deg, "timeline": timeline, "score": score})
    if st.button("➕ Add Another Education Milestone Row"):
        st.session_state.edu_count += 1
        st.rerun()

    # 4. INTERNSHIP EXPERIENCES TRACKING SECTION
    st.markdown("#### 💼 Professional Internship History Block")
    job_data = []
    for i in range(st.session_state.job_count):
        st.markdown(f"*Internship Record #{i+1}*")
        col_jb1, col_jb2 = st.columns(2)
        with col_jb1:
            comp = st.text_input(f"Company / Enterprise Name #{i+1}", key=f"job_comp_{i}")
            role = st.text_input(f"Internship Assigned Designation #{i+1}", key=f"job_role_{i}")
        with col_jb2:
            j_time = st.text_input(f"Employment Duration Tracker #{i+1}", key=f"job_time_{i}", placeholder="e.g., June 2025 - Aug 2025")
            j_details = st.text_area(f"Key Operational Responsibilities & Deliverables #{i+1}", key=f"job_det_{i}")
        job_data.append({"company": comp, "role": role, "timeline": j_time, "details": j_details})
    if st.button("➕ Add Another Internship Record Row"):
        st.session_state.job_count += 1
        st.rerun()

    # 5. GRANULAR TECHNICAL SKILLS SPLIT CATEGORIES
    st.markdown("#### 🛠️ Core Technical Skills Matrix")
    sk_lang = st.text_input("Core Programming Languages", placeholder="e.g., Python, Java, C")
    sk_db = st.text_input("Relational / Non-Relational Database Engines", placeholder="e.g., MySQL, Oracle, MongoDB")
    sk_tools = st.text_area("Developer Tools, Libraries & Frameworks", placeholder="e.g., Git, VS Code, pandas, NumPy, Matplotlib")

    # 6. DISTINCT TECHNICAL PROJECTS PORTFOLIO
    st.markdown("#### 💻 Engineering Projects Portfolio Log")
    proj_data = []
    for i in range(st.session_state.proj_count):
        st.markdown(f"*Project Framework Specifications #{i+1}*")
        p_title = st.text_input(f"Project Title Label #{i+1}", key=f"proj_title_{i}")
        p_tech = st.text_input(f"Technology Stack Modules Utilized #{i+1}", key=f"proj_tech_{i}", placeholder="e.g., Python, Streamlit, Gemini API")
        p_desc = st.text_area(f"Core Functional Scope Explanations #{i+1}", key=f"proj_desc_{i}")
        proj_data.append({"title": p_title, "tech": p_tech, "description": p_desc})
    if st.button("➕ Add Another Technical Project Space"):
        st.session_state.proj_count += 1
        st.rerun()

    # 7. EXTRAS & VERIFIED CREDENTIALS
    st.markdown("#### 🏅 Professional Certifications Log")
    cert_data = []
    for i in range(st.session_state.cert_count):
        c_name = st.text_input(f"Certification Title / Authority #{i+1}", key=f"cert_name_{i}")
        cert_data.append(c_name)
    if st.button("➕ Add Another Certification Row"):
        st.session_state.cert_count += 1
        st.rerun()

    st.write("---")
    generate_btn = st.button("✨ Compile One-Page Corporate Resume Template Layout", type="primary")

with col_viewport:
    st.markdown("### 🖥️ Single-Page Verified Layout Matrix Preview")
    
    if generate_btn:
        if not user_name or not target_role:
            st.warning("⚠️ Full Candidate Name and Target Position parameters are mandatory inputs.")
        else:
            with st.spinner("Executing dynamic single-page content balancing optimization..."):
                try:
                    # Construct structural prompt blocks enforcing space-optimized template formatting rules
                    prompt = f"""
                    You are an expert technical resume formatter. Reconstruct the provided user profiles into an exceptional, executive-tier developer resume layout.
                    
                    CRITICAL CONSTRAINT: Optimize formatting specifically for a strictly single-page format (A4 page budget). Keep content highly impactful, concise, and structured. Eliminate wordy prose.
                    
                    INPUT CHANNELS:
                    - Candidate Name: {user_name}
                    - Contact Matrix: Phone: {p_phone} | Email: {p_email} | Location: {p_loc}
                    - URLs: GitHub: {p_git} | LinkedIn: {p_link}
                    - Target Track: {target_role}
                    
                    ACADEMIC LOGS: {edu_data}
                    INTERNSHIP STREAMS: {job_data}
                    CORE CAPABILITIES SCHEMA:
                    - Languages: {sk_lang}
                    - Databases: {sk_db}
                    - Tools/Libraries: {sk_tools}
                    
                    PORTFOLIO RUNTIMES: {proj_data}
                    VERIFIED CREDENTIALS: {cert_data}
                    
                    SCANNED EXTRA CONTEXT BASE TEXT:
                    {parsed_resume_text}
                    
                    TEMPLATE GEOMETRY LOGIC FORMAT:
                    Output your response completely in clean text markdown strictly using the layout template below. Do not output metadata or conversational greetings:
                    
                    # {user_name.upper()}
                    {p_email} | {p_phone} | {p_loc}
                    GitHub: {p_git} | LinkedIn: {p_link}
                    
                    ## Professional Summary
                    (Provide a strong 2-sentence target summary for an elite '{target_role}' role.)
                    
                    ## Education
                    (For each item in academic logs, list clean single-line bullet entries format):
                    * **Degree / Standard** from **Institution** ({timeline}) - Score / Grade: {score}
                    
                    ## Internship Experience
                    (For each operational item in internship records, output condensed action bullets using the STAR methodology):
                    * **Role Designation** at **Company** ({timeline})
                      - (Action item detail focusing on key operations and tools used)
                    
                    ## Technical Projects
                    (For each entry in project items, format concise action bullets using the STAR method):
                    * **Project Title** | *Tech Stack: {tech}*
                      - (Provide 2 short, metrics-focused bullet items describing performance optimizations or feature development)
                    
                    ## Technical Skills
                    **Languages:** {sk_lang}
                    **Databases:** {sk_db}
                    **Tools & Libraries:** {sk_tools}
                    
                    ## Certifications
                    (List clean bullet rows covering certified data fields directly from user logs)
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    st.session_state.ai_output_cache = response.text
                    st.balloons()
                except Exception as ex:
                    st.error(f"Inference Generation Fault: {ex}")

    # Render Document Preview and Actions if Data Cache Exists
    if st.session_state.ai_output_cache:
        st.success("🎉 Single-Page Balancing Layout Successfully Compiled!")
        
        # Action Block: Build File Attachment Stream
        with st.spinner("Rendering single-page A4 PDF binary streams..."):
            pdf_bytes = compile_one_page_pdf(st.session_state.ai_output_cache)
            
        st.download_button(
            label="📥 Download Strict Single-Page Resume PDF",
            data=pdf_bytes,
            file_name=f"{user_name.replace(' ', '_')}_Final_Resume.pdf",
            mime="application/pdf",
            type="secondary"
        )
        
        st.write("---")
        
        # Emulate page formatting within standard browser workspace view
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding:30px; border-radius:8px; border: 1px solid #ced4da; box-shadow: 0 4px 8px rgba(0,0,0,0.06); color: #000000; font-family: Arial, sans-serif; white-space: pre-wrap; font-size:13.5px; line-height:1.4;">
                {st.session_state.ai_output_cache}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("💡 Fill out the custom blank data forms on the left side, append an optional text resume file to scan data points, and click the compilation button to populate your strict single-page document.")
