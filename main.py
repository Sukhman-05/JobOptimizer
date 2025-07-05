import streamlit as st
import PyPDF2
import io
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import subprocess
import tempfile

load_dotenv()

st.set_page_config(page_title="AI Resume Optimizer", page_icon="📝", layout="wide")

st.title("AI Resume Optimizer")
st.markdown("Upload your resume, job description, and cover letters to generate optimized resumes and cover letters")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize session state
if 'cover_letters' not in st.session_state:
    st.session_state.cover_letters = []
if 'writing_style_analyzed' not in st.session_state:
    st.session_state.writing_style_analyzed = False
if 'writing_style_summary' not in st.session_state:
    st.session_state.writing_style_summary = ""
if 'resume_content' not in st.session_state:
    st.session_state.resume_content = ""

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file is None:
            return ""
        
        if uploaded_file.type == "application/pdf":
            return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
        else:
            content = uploaded_file.read().decode("utf-8")
            return content if content else ""
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return ""

def analyze_writing_style(cover_letters):
    """Analyze writing style from cover letters"""
    if not cover_letters:
        return "No cover letters provided for analysis."
    
    combined_text = "\n\n".join(cover_letters)
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert writing analyst. Analyze the writing style and tone of the provided cover letters."},
            {"role": "user", "content": f"""Analyze the writing style, tone, and characteristics of these cover letters. Focus on:
            1. Writing tone (formal, conversational, confident, etc.)
            2. Sentence structure and complexity
            3. Vocabulary level and technical terms used
            4. Personal voice and unique characteristics
            5. How achievements are described
            6. Overall writing personality
            
            Cover Letters:
            {combined_text}
            
            Provide a concise summary of the writing style that can be used to maintain consistency in future writing."""}
        ],
        temperature=0.3,
        max_tokens=500
    )
    return response.choices[0].message.content

def generate_optimized_resume(resume_content, job_description, writing_style, output_format="latex"):
    """Generate optimized resume based on job description and writing style"""
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    if output_format == "latex":
        system_prompt = """You are an expert resume writer and LaTeX specialist. Generate an optimized one-page resume in LaTeX format.
        
        CRITICAL REQUIREMENTS:
        - Use ONLY the information provided in the user's actual resume content
        - DO NOT invent, fabricate, or add any information not present in the original resume
        - Return ONLY the LaTeX content (no preamble, no document class, no begin/end document)
        - Use the following custom LaTeX commands for proper formatting:
          * \\resumeSubheading{Job Title}{Date}{Company}{Location} for experience entries
          * \\resumeItem{achievement description} for bullet points
          * \\resumeProjectHeading{Project Name | Technologies}{} for project entries
          * \\resumeSubHeadingListStart and \\resumeSubHeadingListEnd for experience AND projects sections
          * \\resumeItemListStart and \\resumeItemListEnd for bullet point lists
          * \\resumeSubSubheading{Subtitle}{Date} for subsections
        - For Projects section: Include \\vspace{-15pt} after each \\resumeItemListEnd (between projects only)
        - Generate at least 3 relevant bullet points for each experience/project entry
        - Use XY format for bullet points (e.g., "Developed X using Y" or "Implemented X that resulted in Y")
        - Organize content into sections: Technical Skills, Experience, Projects, Extracurriculars, Education
        - Keep it to one page
        - Include relevant keywords from the job description
        - Maintain all factual information from the original resume"""
    else:
        system_prompt = """You are an expert resume writer. Generate an optimized one-page resume.
        
        CRITICAL REQUIREMENTS:
        - Use ONLY the information provided in the user's actual resume content
        - DO NOT invent, fabricate, or add any information not present in the original resume
        - Reorganize and optimize the existing content for the job description
        - Maintain all factual information from the original resume
        - Focus on achievements and quantifiable results
        - Match the user's writing style and tone
        - Optimize for the specific job description
        - Clear, professional formatting
        - Relevant keywords from the job description"""
    
    prompt = f"""Create an optimized resume based on the following:

    Original Resume Content:
    {resume_content}

    Target Job Description:
    {job_description}

    Writing Style Analysis:
    {writing_style}

    CRITICAL INSTRUCTIONS:
    - Use ONLY the information from the original resume content above
    - DO NOT invent, fabricate, or add any information not present in the original resume
    - Reorganize and optimize the existing content for the job description
    - Maintain all factual information from the original resume
    - Focus on relevant achievements and skills from the actual resume
    - Use action verbs and quantifiable results from the original content
    - Include keywords from the job description
    - Keep it concise and impactful
    - Ensure it fits on one page

    FORMATTING REQUIREMENTS:
    Use these exact LaTeX commands for proper formatting:
    
    For Experience sections:
    \\resumeSubHeadingListStart
    \\resumeSubheading{{Job Title}}{{Date Range}}
    {{Company Name}}{{Location}}
    \\resumeItemListStart
    \\resumeItem{{Developed X using Y technology that resulted in Z improvement}}
    \\resumeItem{{Implemented X system that increased Y by Z percentage}}
    \\resumeItem{{Led X initiative using Y methodology to achieve Z outcome}}
    \\resumeItemListEnd
    \\resumeSubHeadingListEnd
    
    For Projects section (MUST include \\resumeSubHeadingListStart/End and \\vspace{{-15pt}}):
    \\section{{Projects}}
    \\resumeSubHeadingListStart
    \\resumeProjectHeading{{\\textbf{{Project Name}} $|$ \\emph{{Technologies}}}}{{}}
    \\resumeItemListStart
    \\resumeItem{{Developed X application using Y framework that achieved Z functionality}}
    \\resumeItem{{Implemented X feature using Y technology to improve Z performance}}
    \\resumeItem{{Designed X system using Y methodology to solve Z problem}}
    \\resumeItemListEnd
    \\vspace{{-15pt}}
    
    \\resumeProjectHeading{{\\textbf{{Another Project}} $|$ \\emph{{Different Technologies}}}}{{}}
    \\resumeItemListStart
    \\resumeItem{{Built X platform using Y tools that enabled Z capabilities}}
    \\resumeItem{{Created X solution using Y approach that resulted in Z benefits}}
    \\resumeItem{{Developed X feature using Y technology to enhance Z experience}}
    \\resumeItemListEnd
    \\vspace{{-15pt}}
    \\resumeSubHeadingListEnd
    For Skills section:
    \\section{{Technical Skills}}
    \\begin{{itemize}}[leftmargin=0.15in, label={{}}]
    \\small{{\\item{{
    \\textbf{{Programming Languages:}} Python, Java, C, JavaScript, SQL, HTML/CSS \\\\
    \\textbf{{Frameworks/Technologies:}} React, React Native, FastAPI, Express.js, Node.js, GitHub Pages\\\\
    \\textbf{{Libraries:}} Pandas, Pydantic, Dash, JWT, Bcrypt \\\\
    \\textbf{{Tools:}} Git, MongoDB, Mongoose, RESTful APIs, Streamlit, Vite, Excel, Webflow, WordPress\\\\
    \\textbf{{Exploring/Currently Learning:}} Pytorch, TensorFlow \\\\
    \\textbf{{Spoken Languages:}} English, French, Italian, Punjabi, Hindi
    }}}}
    \\end{{itemize}}
    \\vspace{{-16pt}}

    Generate the optimized resume in {output_format.upper()} format using ONLY the information provided in the original resume and the custom LaTeX commands above."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content

def generate_cover_letter(resume_content, job_description, writing_style, company_name="", job_title=""):
    """Generate a detailed cover letter following the user's writing style"""
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    system_prompt = """You are an expert cover letter writer. Generate a detailed, one-page cover letter that follows the user's writing style.

    CRITICAL REQUIREMENTS:
    - Use ONLY the information provided in the user's actual resume content
    - DO NOT invent, fabricate, or add any information not present in the original resume
    - Must be exactly one page
    - NO EM DASHES (use regular dashes or other punctuation)
    - Must end with: "Thank you for taking the time to consider my application." + newline + "Sincerely," + newline + "Sukhman Singh"
    - Must have 5 distinct paragraphs: Introduction, Academics, Work Experience, Projects, Conclusion
    - Introduction: Talk about skills that make you a good candidate (based on actual resume)
    - Other paragraphs: Show how you gained/applied those skills in real life (using actual experiences from resume)
    - Match the user's writing style and tone exactly
    - Use specific examples and achievements from the actual resume
    - Professional but engaging tone
    - Focus on relevant skills for the job description
    - Maintain all factual information from the original resume"""
    
    prompt = f"""Create a detailed cover letter based on the following:

    Resume Content:
    {resume_content}

    Job Description:
    {job_description}

    Writing Style Analysis:
    {writing_style}

    Company Name: {company_name}
    Job Title: {job_title}

    CRITICAL INSTRUCTIONS:
    - Use ONLY the information from the resume content above
    - DO NOT invent, fabricate, or add any information not present in the original resume
    - Base all content on actual experiences, skills, and achievements from the resume
    - Maintain all factual information from the original resume

    REQUIREMENTS:
    1. Introduction: Discuss skills that make you a strong candidate for this role (based on actual resume)
    2. Academics: Show how your academic background demonstrates relevant skills (from actual resume)
    3. Work Experience: Demonstrate how your work experience applies to this position (from actual resume)
    4. Projects: Highlight specific projects that showcase relevant abilities (from actual resume)
    5. Conclusion: Summarize why you're the ideal candidate (based on actual resume)

    FORMATTING:
    - One page maximum
    - NO EM DASHES (use regular dashes or other punctuation)
    - End with: "Thank you for taking the time to consider my application." + newline + "Sincerely," + newline + "Sukhman Singh"
    - Professional formatting with clear paragraph breaks
    - Match the user's writing style and tone

    Generate a compelling cover letter using ONLY the information provided in the resume content."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

def create_latex_document(content):
    """Create a complete LaTeX document with the provided content"""
    latex_template = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{fontawesome5}
\usepackage{multicol}
\setlength{\multicolsep}{-3.0pt}
\setlength{\columnsep}{-1pt}
\input{glyphtounicode}

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.19in}
\addtolength{\topmargin}{-.7in}
\addtolength{\textheight}{1.4in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\classesList}[4]{
    \item\small{
        {#1 #2 #3 #4 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & \textbf{\small #2} \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{1.001\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & \textbf{\small #2}\\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemi{$\vcenter{\hbox{\tiny$\bullet$}}$}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING----------
\begin{center}
    {\Huge \scshape Sukhman Singh} \\ \vspace{5pt}
    \small \raisebox{-0.2\height}{(226)820-6632} ~ \href{mailto:sing1248@mylaurier.ca}{\raisebox{-0.2\height} {sing1248@mylaurier.ca}} ~
    \href{https://linkedin.com/in/sukhman000/}{\raisebox{-0.2\height}{\underline{Linkedin}}}  ~
    \href{https://github.com/Sukhman-05}{\raisebox{-0.2\height}{\underline{Github}}}
    \vspace{-8pt}
\end{center}

""" + content + r"""

\end{document}"""
    return latex_template

def compile_latex_to_pdf(latex_content, filename="resume"):
    """Compile LaTeX content to PDF"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the LaTeX file
            latex_file = Path(temp_dir) / f"{filename}.tex"
            with open(latex_file, 'w') as f:
                f.write(latex_content)
            
            # Compile using xelatex
            result = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', str(latex_file)],
                cwd=temp_dir,
                capture_output=True,
                text=True
            )
            
            # Check if compilation was successful
            pdf_file = Path(temp_dir) / f"{filename}.pdf"
            if pdf_file.exists():
                with open(pdf_file, 'rb') as f:
                    return f.read()
            else:
                st.error(f"LaTeX compilation failed: {result.stderr}")
                return None
    except Exception as e:
        st.error(f"Error compiling LaTeX: {str(e)}")
        return None

# Sidebar for cover letter management
with st.sidebar:
    st.header("📝 Cover Letter Management")
    
    # Upload cover letters
    uploaded_cover_letters = st.file_uploader(
        "Upload your cover letters (PDF or TXT)", 
        type=["pdf", "txt"], 
        accept_multiple_files=True,
        help="Upload multiple cover letters to help the AI learn your writing style"
    )
    
    if uploaded_cover_letters:
        for file in uploaded_cover_letters:
            if file not in [cl['file'] for cl in st.session_state.cover_letters]:
                content = extract_text_from_file(file)
                st.session_state.cover_letters.append({
                    'file': file,
                    'content': content,
                    'name': file.name
                })
    
    # Display uploaded cover letters
    if st.session_state.cover_letters:
        st.subheader("Uploaded Cover Letters:")
        for i, cl in enumerate(st.session_state.cover_letters):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {cl['name']}")
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.cover_letters.pop(i)
                    st.rerun()
    
    # Analyze writing style button
    if st.session_state.cover_letters and not st.session_state.writing_style_analyzed:
        if st.button("Analyze Writing Style"):
            with st.spinner("Analyzing your writing style..."):
                cover_letter_texts = [cl['content'] for cl in st.session_state.cover_letters]
                st.session_state.writing_style_summary = analyze_writing_style(cover_letter_texts)
                st.session_state.writing_style_analyzed = True
                st.success("Writing style analyzed!")
    
    # Display writing style summary
    if st.session_state.writing_style_analyzed:
        st.subheader("Writing Style Analysis:")
        st.info(st.session_state.writing_style_summary)

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.header("📄 Resume Input")
    uploaded_resume = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
    
    if uploaded_resume:
        # Store resume content in session state to avoid reading file twice
        if 'current_resume_file' not in st.session_state or st.session_state.current_resume_file != uploaded_resume.name:
            st.session_state.resume_content = extract_text_from_file(uploaded_resume)
            st.session_state.current_resume_file = uploaded_resume.name
        
        st.text_area("Resume Content", st.session_state.resume_content, height=200)

with col2:
    st.header("💼 Job Description")
    job_description = st.text_area(
        "Paste the job description here",
        height=200,
        placeholder="Paste the complete job description including requirements, responsibilities, and qualifications..."
    )

# Cover letter specific inputs
st.header("📝 Cover Letter Details")
col3, col4 = st.columns(2)

with col3:
    company_name = st.text_input("Company Name", placeholder="e.g., Google, Microsoft, etc.")
    job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer, Data Scientist, etc.")

with col4:
    generate_cover_letter_option = st.checkbox("Generate Cover Letter", value=True, help="Generate a cover letter along with the optimized resume")

# Output options
st.header("🎯 Output Options")
output_format = st.selectbox(
    "Choose output format:",
    ["latex", "pdf", "text"],
    help="LaTeX: Returns LaTeX code without preamble. PDF: Downloads compiled PDF. Text: Plain text version."
)

# Generate button
if st.button("🚀 Generate Optimized Resume", type="primary"):
    if not uploaded_resume:
        st.error("Please upload a resume first.")
    elif not job_description:
        st.error("Please provide a job description.")
    elif not st.session_state.writing_style_analyzed and st.session_state.cover_letters:
        st.warning("Please analyze your writing style first using the sidebar.")
    else:
        with st.spinner("Generating optimized resume..."):
            try:
                # Use stored resume content from session state
                resume_content = st.session_state.resume_content
                
                # Check if resume content is empty
                if not resume_content or not resume_content.strip():
                    st.error("The uploaded resume appears to be empty or could not be read. Please upload a valid resume file.")
                    st.stop()
                
                # Check if job description is empty
                if not job_description or not job_description.strip():
                    st.error("Please provide a job description to optimize the resume for.")
                    st.stop()
                
                # Use writing style if available, otherwise use default
                writing_style = st.session_state.writing_style_summary if st.session_state.writing_style_analyzed else "Professional and achievement-focused writing style."
                
                # Generate optimized resume
                optimized_content = generate_optimized_resume(
                    resume_content, 
                    job_description, 
                    writing_style,
                    output_format
                )
                
                st.success("Optimized resume generated!")
                
                # Display resume results based on format
                if output_format == "latex":
                    st.subheader("📄 LaTeX Code (Copy this content):")
                    st.code(optimized_content, language="latex")
                    
                    # Option to download as PDF
                    if st.button("📥 Download Resume as PDF"):
                        complete_latex = create_latex_document(optimized_content)
                        pdf_data = compile_latex_to_pdf(complete_latex)
                        if pdf_data:
                            st.download_button(
                                label="📄 Download Resume PDF",
                                data=pdf_data,
                                file_name="optimized_resume.pdf",
                                mime="application/pdf"
                            )
                
                elif output_format == "pdf":
                    complete_latex = create_latex_document(optimized_content)
                    pdf_data = compile_latex_to_pdf(complete_latex)
                    if pdf_data:
                        st.download_button(
                            label="📄 Download Optimized Resume PDF",
                            data=pdf_data,
                            file_name="optimized_resume.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Failed to generate PDF. Please try LaTeX format instead.")
                
                else:  # text format
                    st.subheader("📄 Optimized Resume:")
                    st.text_area("Optimized Content", optimized_content, height=400)
                
                # Generate cover letter if requested
                if generate_cover_letter_option:
                    st.markdown("---")
                    st.subheader("📝 Generating Cover Letter...")
                    
                    with st.spinner("Creating personalized cover letter..."):
                        cover_letter_content = generate_cover_letter(
                            resume_content,
                            job_description,
                            writing_style,
                            company_name,
                            job_title
                        )
                    
                    st.success("Cover letter generated!")
                    
                    # Display cover letter
                    st.subheader("📝 Cover Letter:")
                    st.text_area("Cover Letter Content", cover_letter_content, height=400)
                    
                    # Download cover letter as text
                    if cover_letter_content:
                        st.download_button(
                            label="📄 Download Cover Letter",
                            data=cover_letter_content,
                            file_name="cover_letter.txt",
                            mime="text/plain"
                        )
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Instructions
with st.expander("📋 How to Use"):
    st.markdown("""
    ### Step-by-Step Instructions:
    
    1. **Upload Cover Letters** (Sidebar): Upload multiple cover letters to help the AI learn your writing style
    2. **Analyze Writing Style**: Click the "Analyze Writing Style" button in the sidebar
    3. **Upload Resume**: Upload your current resume in PDF or TXT format
    4. **Add Job Description**: Paste the complete job description you're targeting
    5. **Cover Letter Details**: Enter company name and job title (optional but recommended)
    6. **Choose Output Format**:
       - **LaTeX**: Returns LaTeX code without preamble (minimal tokens)
       - **PDF**: Downloads compiled PDF file
       - **Text**: Plain text version
    7. **Generate**: Click "Generate Optimized Resume"
    
    ### Features:
    - **Writing Style Learning**: The AI analyzes your cover letters to maintain your unique voice
    - **Job-Specific Optimization**: Tailors content to match the job description
    - **Cover Letter Generation**: Creates detailed, personalized cover letters
    - **Multiple Output Formats**: Choose what works best for your workflow
    - **Token Efficiency**: LaTeX format returns only the content, not the preamble
    
    ### Cover Letter Features:
    - **One-page format** with professional structure
    - **5 distinct paragraphs**: Introduction, Academics, Work Experience, Projects, Conclusion
    - **Skills-focused**: Introduction discusses relevant skills, other paragraphs show real-world application
    - **No em dashes**: Uses regular dashes or other punctuation
    - **Consistent closing**: "Thank you for taking the time to consider my application.\\nSincerely,\\nSukhman Singh"
    """)