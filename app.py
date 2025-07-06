from flask import Flask, render_template, request, jsonify, send_file
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
import tomllib
import base64

load_dotenv()

app = Flask(__name__)

# Load API key from environment variable only
def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set")
    return api_key

OPENAI_API_KEY = get_openai_api_key()

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
        return f"Error reading PDF: {str(e)}"

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

def generate_optimized_resume(resume_content, job_description, writing_style, output_format="text"):
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
    - Ensure it fits on one page"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    return response.choices[0].message.content

def generate_cover_letter(resume_content, job_description, writing_style, company_name="", job_title=""):
    """Generate cover letter based on resume, job description, and writing style"""
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""Create a compelling cover letter based on the following:

    Resume Content:
    {resume_content}

    Job Description:
    {job_description}

    Writing Style Analysis:
    {writing_style}

    Company: {company_name}
    Job Title: {job_title}

    CRITICAL INSTRUCTIONS:
    - Use ONLY the information from the original resume content above
    - DO NOT invent, fabricate, or add any information not present in the original resume
    - Match the user's writing style and tone
    - Focus on relevant achievements and skills from the actual resume
    - Address the specific job requirements
    - Keep it concise and impactful (1 page maximum)
    - Professional and engaging tone
    - Include specific examples from the resume that match the job requirements"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert cover letter writer. Create compelling, personalized cover letters that match the user's writing style."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1500
    )
    return response.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze-writing-style', methods=['POST'])
def analyze_writing_style_api():
    try:
        data = request.get_json()
        cover_letters = data.get('cover_letters', [])
        
        if not cover_letters:
            return jsonify({'error': 'No cover letters provided'}), 400
        
        analysis = analyze_writing_style(cover_letters)
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-resume', methods=['POST'])
def generate_resume_api():
    try:
        data = request.get_json()
        resume_content = data.get('resume_content', '')
        job_description = data.get('job_description', '')
        writing_style = data.get('writing_style', '')
        output_format = data.get('output_format', 'text')
        
        if not resume_content or not job_description:
            return jsonify({'error': 'Resume content and job description are required'}), 400
        
        optimized_resume = generate_optimized_resume(resume_content, job_description, writing_style, output_format)
        return jsonify({'resume': optimized_resume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter_api():
    try:
        data = request.get_json()
        resume_content = data.get('resume_content', '')
        job_description = data.get('job_description', '')
        writing_style = data.get('writing_style', '')
        company_name = data.get('company_name', '')
        job_title = data.get('job_title', '')
        
        if not resume_content or not job_description:
            return jsonify({'error': 'Resume content and job description are required'}), 400
        
        cover_letter = generate_cover_letter(resume_content, job_description, writing_style, company_name, job_title)
        return jsonify({'cover_letter': cover_letter})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-text', methods=['POST'])
def extract_text_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file.content_type == "application/pdf":
            text = extract_text_from_pdf(io.BytesIO(file.read()))
        else:
            text = file.read().decode("utf-8")
        
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 