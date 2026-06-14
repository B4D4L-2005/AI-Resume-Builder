import os
import sys
import warnings
import json
from io import BytesIO
from pypdf import PdfReader
from fpdf import FPDF

# 1. Intercept platform loop anomalies and warnings
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
from google import genai

# 2. Page Configuration (Clean corporate light theme)
st.set_page_config(
    page_title="ResumeAI - ATS Optimizer",
    page_icon="🚀",
    layout="wide"
)

# 3. Secure API Initialization via Environment Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")
client = None
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
    pdf = StrictSinglePagePDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=12, top=10, right=12)
    pdf.add_page()

    clean_text = markdown_text.encode('latin-1', 'replace').decode('latin-1')
    lines = clean_text.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(1.5)
            continue

        if stripped.startswith('# '):
            pdf.set_font("Arial", "B", 15)
            pdf.cell(0, 7, stripped.replace('# ', '').strip(), ln=1, align="C")
        elif stripped.startswith('## '):
            pdf.ln(2)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 5, stripped.replace('## ', '').strip().upper(), ln=1)
            pdf.line(12, pdf.get_y(), 198, pdf.get_y())
            pdf.ln(1)
        elif stripped.startswith('* ') or stripped.startswith('- '):
            pdf.set_font("Arial", "", 9.5)
            bullet_text = stripped[2:].strip()
            # Strip markdown bold markers since FPDF base font won't render **
            bullet_text = bullet_text.replace('**', '').replace('*', '')
            pdf.cell(4, 4.5, chr(149), ln=0)
            pdf.multi_cell(0, 4.5, bullet_text)
        else:
            pdf.set_font("Arial", "", 9.5)
            cleaned = stripped.replace('**', '').replace('*', '')
            if "|" in cleaned:
                pdf.cell(0, 4.5, cleaned, ln=1, align="C")
            else:
                pdf.multi_cell(0, 4.5, cleaned)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- DEFAULT DATA SCHEMA ---
DEFAULT_USER_DATA = {
    "name": "", "email": "", "phone": "", "location": "", "github": "", "linkedin": "", "target_role": "",
    "edu_inst_0": "", "edu_deg_0": "", "edu_time_0": "", "edu_score_0": "",
    "job_comp_0": "", "job_role_0": "", "job_time_0": "", "job_det_0": "",
    "sk_lang": "", "sk_db": "", "sk_tools": "",
    "proj_title_0": "", "proj_tech_0": "", "proj_desc_0": "",
    "cert_name_0": ""
}

# --- CONTEXT PERSISTENCE MATRIX ---
if "user_data" not in st.session_state:
    st.session_state.user_data = dict(DEFAULT_USER_DATA)
if "edu_count" not in st.session_state: st.session_state.edu_count = 1
if "job_count" not in st.session_state: st.session_state.job_count = 1
if "proj_count" not in st.session_state: st.session_state.proj_count = 1
if "cert_count" not in st.session_state: st.session_state.cert_count = 1
if "final_output" not in st.session_state: st.session_state.final_output = None
if "ats_analysis" not in st.session_state: st.session_state.ats_analysis = None
if "debug_raw_text" not in st.session_state: st.session_state.debug_raw_text = ""
if "debug_ai_response" not in st.session_state: st.session_state.debug_ai_response = ""


def ensure_field(key, default=""):
    """Make sure a dynamically-indexed field exists in session_state.user_data."""
    if key not in st.session_state.user_data:
        st.session_state.user_data[key] = default


def extract_json_block(raw_text):
    """Robustly pull a JSON object out of an LLM response, even with extra text/fences."""
    text = raw_text.strip()
    text = text.replace("```json", "").replace("```JSON", "").replace("```", "")
    # Find the first '{' and the last '}' to isolate the JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in AI response.")
    json_str = text[start:end + 1]
    return json.loads(json_str)


# --- APP INTERFACE HEADER ---
st.markdown(
    """
    <div style="background-color:#f8f9fa; padding:25px; border-radius:12px; text-align:center; border: 1px solid #e9ecef; margin-bottom: 20px;">
        <h1 style="color:#1e3a8a; font-size:38px; margin:0 0 5px 0;">🚀 ResumeAI Core Platform</h1>
        <p style="color:#4b5563; font-size:16px; margin:0;">
            Intelligent AI parsing agent that extracts your raw resume data points and optimizes structural templates
            so your resume is far easier to shortlist during automated resume scanning.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

col_workspace, col_viewport = st.columns([1.1, 1.2])

with col_workspace:
    st.markdown("### 📥 Profile Input Workspace")

    # ADVANCED FEATURE: AI PARSING AGENT
    uploaded_file = st.file_uploader("Upload an existing PDF resume to trigger AI Auto-Fill", type=["pdf"])

    if uploaded_file is not None and st.button("🤖 Analyze & Auto-Fill All Form Fields Below"):
        with st.spinner("AI parsing agent reading and extracting fields..."):
            try:
                reader = PdfReader(uploaded_file)
                raw_text = ""
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        raw_text += content + "\n"

                if not raw_text.strip():
                    st.error("⚠️ No selectable text found in this PDF. It may be a scanned/image-based resume.")
                else:
                    st.session_state.debug_raw_text = raw_text

                    # Execute Structured Parsing Handshake with Gemini
                    parse_prompt = f"""
You are an advanced resume extraction model. Read the unstructured resume text below carefully and
extract EVERY available entry (do not limit to one or two — extract ALL education entries, ALL
internships/jobs, ALL projects, and ALL certifications found in the text).

Output a single JSON object with EXACTLY this structure:

{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "github": "",
  "linkedin": "",
  "target_role": "",
  "sk_lang": "",
  "sk_db": "",
  "sk_tools": "",
  "education": [
    {{"institution": "", "degree": "", "timeline": "", "score": ""}}
  ],
  "internships": [
    {{"company": "", "role": "", "timeline": "", "details": ""}}
  ],
  "projects": [
    {{"title": "", "tech": "", "description": ""}}
  ],
  "certifications": ["", ""]
}}

RULES:
- "education", "internships", "projects", "certifications" are ARRAYS — include ONE array element for EVERY entry found in the resume, in the order they appear. Do not cap the count.
- "target_role" should be inferred from the candidate's most recent role, objective/summary line, or strongest skill area if not explicitly stated.
- "tech" for each project should list the technology stack used (comma separated), inferred from the description if not explicitly labeled.
- "description" for each project should be a concise 1-3 sentence summary of what it does and the candidate's contribution/impact.
- "details" for each internship/job should summarize key responsibilities/achievements as plain text (use \\n between points if multiple).
- "certifications" is an array of plain strings, one per certification.
- If a field or section is genuinely not present anywhere in the text, use an empty string "" (or empty array []  for missing sections). Never invent data.
- Output ONLY the raw JSON object. No markdown fences, no commentary, no explanation before or after.

UNSTRUCTURED RESUME TEXT:
\"\"\"{raw_text}\"\"\"
"""

                    parse_response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=parse_prompt,
                    )

                    st.session_state.debug_ai_response = parse_response.text

                    parsed_json = extract_json_block(parse_response.text)

                    # --- Simple scalar fields ---
                    for key in ["name", "email", "phone", "location", "github", "linkedin",
                                "target_role", "sk_lang", "sk_db", "sk_tools"]:
                        if key in parsed_json and parsed_json[key] is not None:
                            st.session_state.user_data[key] = parsed_json[key]

                    # --- Education array -> edu_inst_N, edu_deg_N, edu_time_N, edu_score_N ---
                    edu_list = parsed_json.get("education") or []
                    for idx, entry in enumerate(edu_list):
                        if not isinstance(entry, dict):
                            continue
                        st.session_state.user_data[f"edu_inst_{idx}"] = entry.get("institution", "") or ""
                        st.session_state.user_data[f"edu_deg_{idx}"] = entry.get("degree", "") or ""
                        st.session_state.user_data[f"edu_time_{idx}"] = entry.get("timeline", "") or ""
                        st.session_state.user_data[f"edu_score_{idx}"] = entry.get("score", "") or ""
                    if edu_list:
                        st.session_state.edu_count = max(st.session_state.edu_count, len(edu_list))

                    # --- Internships array -> job_comp_N, job_role_N, job_time_N, job_det_N ---
                    job_list = parsed_json.get("internships") or []
                    for idx, entry in enumerate(job_list):
                        if not isinstance(entry, dict):
                            continue
                        st.session_state.user_data[f"job_comp_{idx}"] = entry.get("company", "") or ""
                        st.session_state.user_data[f"job_role_{idx}"] = entry.get("role", "") or ""
                        st.session_state.user_data[f"job_time_{idx}"] = entry.get("timeline", "") or ""
                        st.session_state.user_data[f"job_det_{idx}"] = entry.get("details", "") or ""
                    if job_list:
                        st.session_state.job_count = max(st.session_state.job_count, len(job_list))

                    # --- Projects array -> proj_title_N, proj_tech_N, proj_desc_N ---
                    proj_list = parsed_json.get("projects") or []
                    for idx, entry in enumerate(proj_list):
                        if not isinstance(entry, dict):
                            continue
                        st.session_state.user_data[f"proj_title_{idx}"] = entry.get("title", "") or ""
                        st.session_state.user_data[f"proj_tech_{idx}"] = entry.get("tech", "") or ""
                        st.session_state.user_data[f"proj_desc_{idx}"] = entry.get("description", "") or ""
                    if proj_list:
                        st.session_state.proj_count = max(st.session_state.proj_count, len(proj_list))

                    # --- Certifications array -> cert_name_N ---
                    cert_list = parsed_json.get("certifications") or []
                    cert_list = [c for c in cert_list if isinstance(c, str) and c.strip()]
                    for idx, cert_name in enumerate(cert_list):
                        st.session_state.user_data[f"cert_name_{idx}"] = cert_name
                    if cert_list:
                        st.session_state.cert_count = max(st.session_state.cert_count, len(cert_list))

                    st.success("🎉 AI successfully processed the resume and mapped the fields below! Review the forms before optimizing.")
                    st.rerun()
            except Exception as parse_ex:
                st.error(f"AI File Processing Error: Ensure your PDF contains searchable text. Error details: {parse_ex}")
                if st.session_state.debug_ai_response:
                    st.warning("The AI did respond — check the debug panel below to see what it returned.")

    if st.session_state.debug_raw_text or st.session_state.debug_ai_response:
        with st.expander("🔍 Debug: Last Upload Parsing Details"):
            if st.session_state.debug_raw_text:
                st.markdown("**Text extracted from PDF:**")
                st.text(st.session_state.debug_raw_text)
            if st.session_state.debug_ai_response:
                st.markdown("**Raw AI extraction response:**")
                st.text(st.session_state.debug_ai_response)

    st.write("---")
    st.markdown("#### 👤 Personal Details")
    user_name = st.text_input("Full Name", value=st.session_state.user_data["name"])
    p_email = st.text_input("Email Address", value=st.session_state.user_data["email"])
    p_phone = st.text_input("Mobile Number", value=st.session_state.user_data["phone"])
    p_loc = st.text_input("Current Location", value=st.session_state.user_data["location"])
    p_git = st.text_input("GitHub Profile URL Link", value=st.session_state.user_data["github"])
    p_link = st.text_input("LinkedIn Profile URL", value=st.session_state.user_data["linkedin"])
    target_role = st.text_input("Target Job Track Position (CRITICAL FOR ATS)", value=st.session_state.user_data["target_role"])

    st.markdown("#### 🎓 Academic History Tracking")
    edu_data = []
    for i in range(st.session_state.edu_count):
        st.markdown(f"**Institution Entry Tier #{i+1}**")
        ensure_field(f"edu_inst_{i}")
        ensure_field(f"edu_deg_{i}")
        ensure_field(f"edu_time_{i}")
        ensure_field(f"edu_score_{i}")
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            inst = st.text_input(f"School / University Name #{i+1}", value=st.session_state.user_data[f"edu_inst_{i}"], key=f"form_inst_{i}")
            deg = st.text_input(f"Degree / Standard #{i+1}", value=st.session_state.user_data[f"edu_deg_{i}"], key=f"form_deg_{i}")
        with col_ed2:
            timeline = st.text_input(f"Timeline Years #{i+1}", value=st.session_state.user_data[f"edu_time_{i}"], key=f"form_time_{i}")
            score = st.text_input(f"CGPA / Percentage #{i+1}", value=st.session_state.user_data[f"edu_score_{i}"], key=f"form_score_{i}")
        edu_data.append({"institution": inst, "degree": deg, "timeline": timeline, "score": score})
    if st.button("➕ Add Another Education Row"):
        st.session_state.edu_count += 1
        st.rerun()

    st.markdown("#### 💼 Professional Internship History Block")
    job_data = []
    for i in range(st.session_state.job_count):
        st.markdown(f"**Internship Record #{i+1}**")
        ensure_field(f"job_comp_{i}")
        ensure_field(f"job_role_{i}")
        ensure_field(f"job_time_{i}")
        ensure_field(f"job_det_{i}")
        col_jb1, col_jb2 = st.columns(2)
        with col_jb1:
            comp = st.text_input(f"Company Name #{i+1}", value=st.session_state.user_data[f"job_comp_{i}"], key=f"form_comp_{i}")
            role = st.text_input(f"Internship Designation #{i+1}", value=st.session_state.user_data[f"job_role_{i}"], key=f"form_role_{i}")
        with col_jb2:
            j_time = st.text_input(f"Employment Duration Tracker #{i+1}", value=st.session_state.user_data[f"job_time_{i}"], key=f"form_jtime_{i}")
            j_details = st.text_area(f"Key Responsibilities #{i+1}", value=st.session_state.user_data[f"job_det_{i}"], key=f"form_jdet_{i}")
        job_data.append({"company": comp, "role": role, "timeline": j_time, "details": j_details})
    if st.button("➕ Add Another Internship Row"):
        st.session_state.job_count += 1
        st.rerun()

    st.markdown("#### 🛠️ Core Technical Skills Matrix")
    sk_lang = st.text_input("Core Programming Languages", value=st.session_state.user_data["sk_lang"])
    sk_db = st.text_input("Databases", value=st.session_state.user_data["sk_db"])
    sk_tools = st.text_area("Tools & Developer Frameworks", value=st.session_state.user_data["sk_tools"])

    st.markdown("#### 💻 Engineering Projects Portfolio")
    proj_data = []
    for i in range(st.session_state.proj_count):
        st.markdown(f"**Project Framework Specifications #{i+1}**")
        ensure_field(f"proj_title_{i}")
        ensure_field(f"proj_tech_{i}")
        ensure_field(f"proj_desc_{i}")
        p_title = st.text_input(f"Project Title Label #{i+1}", value=st.session_state.user_data[f"proj_title_{i}"], key=f"form_ptit_{i}")
        p_tech = st.text_input(f"Technology Stack Modules #{i+1}", value=st.session_state.user_data[f"proj_tech_{i}"], key=f"form_ptech_{i}")
        p_desc = st.text_area(f"Functional Scope #{i+1}", value=st.session_state.user_data[f"proj_desc_{i}"], key=f"form_pdesc_{i}")
        proj_data.append({"title": p_title, "tech": p_tech, "description": p_desc})
    if st.button("➕ Add Another Project Space"):
        st.session_state.proj_count += 1
        st.rerun()

    st.markdown("#### 🏅 Certifications")
    cert_data = []
    for i in range(st.session_state.cert_count):
        ensure_field(f"cert_name_{i}")
        c_name = st.text_input(f"Certification #{i+1}", value=st.session_state.user_data[f"cert_name_{i}"], key=f"form_cname_{i}")
        cert_data.append(c_name)
    if st.button("➕ Add Another Certification Row"):
        st.session_state.cert_count += 1
        st.rerun()

    st.write("---")
    generate_btn = st.button("✨ Optimize Resume for ATS Shortlisting", type="primary")

with col_viewport:
    st.markdown("### 🖥️ Single-Page Verified Layout Matrix Preview")

    if generate_btn:
        if not user_name or not target_role:
            st.warning("⚠️ Candidate Name and Target Position parameters are mandatory inputs.")
        else:
            with st.spinner("AI Engine performing structural ATS scaling calculations..."):
                try:
                    # Build readable text blocks for education/internship/project sections
                    # so the template fills in cleanly without referencing undefined variables.
                    edu_lines = []
                    for e in edu_data:
                        if e["institution"] or e["degree"]:
                            edu_lines.append(
                                f"- Degree/Standard: {e['degree']} | Institution: {e['institution']} | "
                                f"Timeline: {e['timeline']} | Score: {e['score']}"
                            )
                    edu_block = "\n".join(edu_lines) if edu_lines else "No formal education entries provided."

                    job_lines = []
                    for j in job_data:
                        if j["company"] or j["role"]:
                            job_lines.append(
                                f"- Role: {j['role']} | Company: {j['company']} | Duration: {j['timeline']} | "
                                f"Responsibilities: {j['details']}"
                            )
                    job_block = "\n".join(job_lines) if job_lines else "NO INTERNSHIP DATA PROVIDED — omit the 'Internship Experience' section entirely from the output."

                    proj_lines = []
                    for p in proj_data:
                        if p["title"]:
                            proj_lines.append(
                                f"- Title: {p['title']} | Tech Stack: {p['tech']} | Description: {p['description']}"
                            )
                    proj_block = "\n".join(proj_lines) if proj_lines else "No project entries provided."

                    cert_lines = [c for c in cert_data if c.strip()]
                    cert_block = "\n".join(f"- {c}" for c in cert_lines) if cert_lines else "No certifications provided — omit the 'Certifications' section entirely from the output."

                    # Enforce explicit, programmatic optimization directives for ATS-friendly output
                    main_prompt = f"""
You are an elite corporate technical recruiting algorithm architect. Reconstruct the user data below into a
single-page, ATS-friendly developer resume tailored for the role of '{target_role}'.

OPTIMIZATION RULES:
1. Keyword Injection: Naturally weave in industry-standard keywords and skills relevant to a '{target_role}' role so automated scanners match the role profile.
2. STAR Method Alignment: Rewrite Project and Internship bullet points using action-oriented language (Situation, Task, Action, Result) with concrete outcomes, metrics, or scope where plausible. Do not fabricate numbers if none are given — instead emphasize scope, tools, and impact qualitatively.
3. Formatting: Plain linear layout only. No tables, multi-column elements, or special characters that break parsers.
4. Length: Keep content dense and concise enough to fit a single A4 page.
5. If a section has no data (see notes below), OMIT that section heading and content entirely — do not invent placeholder content.

CANDIDATE DATA:
Name: {user_name}
Contact: Email: {p_email} | Phone: {p_phone} | Location: {p_loc}
Links: GitHub: {p_git} | LinkedIn: {p_link}
Target Role: {target_role}

Education entries:
{edu_block}

Internship / Work Experience entries:
{job_block}

Skills — Languages: {sk_lang} | Databases: {sk_db} | Tools/Frameworks: {sk_tools}

Project entries:
{proj_block}

Certifications:
{cert_block}

OUTPUT FORMAT (plain text markdown, no intro/outro commentary, omit any section with no data as instructed above):

# {user_name.upper()}
{p_email} | {p_phone} | {p_loc}
GitHub: {p_git} | LinkedIn: {p_link}

## Professional Summary
(2-3 sentence technical summary tailored to '{target_role}', incorporating relevant keywords.)

## Education
* **Degree/Standard** — **Institution** (Timeline) — Score: value

## Internship Experience
* **Role** at **Company** (Duration)
  - Bullet 1 (STAR-style, action verb first)
  - Bullet 2 (STAR-style, action verb first)

## Technical Projects
* **Project Title** | Tech Stack: list
  - Bullet describing what was built and how
  - Bullet describing outcome/impact/optimization

## Technical Skills
**Languages:** {sk_lang}
**Databases:** {sk_db}
**Tools & Libraries:** {sk_tools}

## Certifications
* Certification name
"""

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=main_prompt,
                    )
                    st.session_state.final_output = response.text

                    # Run a parallel diagnostic assessment to provide section-by-section improvement feedback
                    grade_prompt = f"""
Review the following resume markdown for a '{target_role}' position. Provide a short, encouraging diagnostic
report covering: (1) keyword alignment with the target role, (2) clarity and impact of bullet points,
(3) formatting/ATS-parsability, and (4) one concrete suggestion to strengthen each major section
(Summary, Education, Experience, Projects, Skills — skip any section that doesn't exist).
Write it as a clean, readable paragraph-based report. Do not mention any numeric score or percentage.

RESUME TEXT:
{st.session_state.final_output}
"""
                    grade_response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=grade_prompt,
                    )
                    st.session_state.ats_analysis = grade_response.text
                    st.balloons()
                except Exception as ex:
                    st.error(f"Inference Fault Loop: {ex}")

    # Display Document Preview and Actions if Data Cache Exists
    if st.session_state.final_output:
        st.success("🎉 Optimized ATS-Friendly Resume Successfully Compiled!")

        # Display the Automated Real-Time Feedback Report Panel
        st.markdown("#### 📊 Resume Improvement Report")
        st.info(st.session_state.ats_analysis)

        # Action Block: Build File Attachment Stream
        with st.spinner("Rendering strict single-page A4 PDF binary streams..."):
            pdf_bytes = compile_one_page_pdf(st.session_state.final_output)

        st.download_button(
            label="📥 Download Optimized Single-Page Resume PDF",
            data=pdf_bytes,
            file_name=f"{user_name.replace(' ', '_')}_Optimized_Resume.pdf",
            mime="application/pdf",
            type="primary"
        )

        st.write("---")

        # Emulate page formatting within standard browser workspace view
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding:30px; border-radius:8px; border: 1px solid #ced4da; box-shadow: 0 4px 8px rgba(0,0,0,0.06); color: #000000; font-family: Arial, sans-serif; white-space: pre-wrap; font-size:13.5px; line-height:1.4;">
                {st.session_state.final_output}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("💡 Upload an old text-based PDF resume above to auto-fill your profile layout instantly, adjust details manually, and click the optimize button to generate your ATS-friendly resume.")
