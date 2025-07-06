from flask import Flask, render_template, request, jsonify, send_file, session
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
import uuid
import sqlite3
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS writing_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            analysis TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_resume (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Load API key from environment variable only
def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set")
    return api_key

OPENAI_API_KEY = get_openai_api_key()

def get_or_create_user():
    """Get or create a user session"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        # Create user in database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (session['user_id'],))
        conn.commit()
        conn.close()
    return session['user_id']

def save_cover_letter(user_id, content, filename):
    """Save cover letter to database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cover_letters (user_id, content, filename)
        VALUES (?, ?, ?)
    ''', (user_id, content, filename))
    conn.commit()
    conn.close()

def get_user_cover_letters(user_id):
    """Get all cover letters for a user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM cover_letters WHERE user_id = ?', (user_id,))
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

def save_writing_analysis(user_id, analysis):
    """Save writing style analysis to database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO writing_analysis (user_id, analysis, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, analysis))
    conn.commit()
    conn.close()

def get_writing_analysis(user_id):
    """Get writing style analysis for a user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT analysis FROM writing_analysis WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_master_resume(user_id, content, filename):
    """Save master resume to database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO master_resume (user_id, content, filename)
        VALUES (?, ?, ?)
    ''', (user_id, content, filename))
    conn.commit()
    conn.close()

def get_master_resume(user_id):
    """Get master resume for a user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM master_resume WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

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
    
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
    
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

def generate_optimized_resume(master_resume_content, job_description, writing_style, output_format="text"):
    """Generate optimized resume by editing the master resume for the specific job"""
    
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
    
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
    
    prompt = f"""Create an optimized resume by editing the master resume for this specific job:

    Master Resume Content (Your Complete Resume):
    {master_resume_content}

    Target Job Description:
    {job_description}

    Writing Style Analysis:
    {writing_style}

    CRITICAL INSTRUCTIONS:
    - Use ONLY the information from the master resume content above
    - DO NOT invent, fabricate, or add any information not present in the master resume
    - Edit and reorganize the existing content to match the job requirements
    - Keep relevant experiences and skills, remove or minimize irrelevant ones
    - Maintain all factual information from the master resume
    - Focus on achievements and skills that match the job description
    - Use action verbs and quantifiable results from the original content
    - Include keywords from the job description
    - Keep it concise and impactful (1 page maximum)
    - Prioritize experiences that directly relate to the target role"""

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

def generate_cover_letter(master_resume_content, job_description, writing_style, company_name="", job_title=""):
    """Generate cover letter based on master resume, job description, and writing style"""
    
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""Create a compelling cover letter based on the following:

    Master Resume Content (Your Complete Resume):
    {master_resume_content}

    Job Description:
    {job_description}

    Writing Style Analysis:
    {writing_style}

    Company: {company_name}
    Job Title: {job_title}

    CRITICAL INSTRUCTIONS:
    - Use ONLY the information from the master resume content above
    - DO NOT invent, fabricate, or add any information not present in the master resume
    - Match the user's writing style and tone
    - Focus on relevant achievements and skills from the master resume
    - Address the specific job requirements
    - Keep it concise and impactful (1 page maximum)
    - Professional and engaging tone
    - Include specific examples from the master resume that match the job requirements"""

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
    user_id = get_or_create_user()
    return render_template('index.html', user_id=user_id)

@app.route('/api/upload-cover-letters', methods=['POST'])
def upload_cover_letters_api():
    try:
        user_id = get_or_create_user()
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if file.content_type == "application/pdf":
                content = extract_text_from_pdf(io.BytesIO(file.read()))
            else:
                content = file.read().decode("utf-8")
            
            if content:
                save_cover_letter(user_id, content, file.filename)
                uploaded_files.append(file.filename)
        
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_files)} cover letter(s)',
            'files': uploaded_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-cover-letters', methods=['GET'])
def get_cover_letters_api():
    try:
        user_id = get_or_create_user()
        cover_letters = get_user_cover_letters(user_id)
        return jsonify({'cover_letters': cover_letters})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-writing-style', methods=['POST'])
def analyze_writing_style_api():
    try:
        user_id = get_or_create_user()
        cover_letters = get_user_cover_letters(user_id)
        
        if not cover_letters:
            return jsonify({'error': 'No cover letters found. Please upload cover letters first.'}), 400
        
        analysis = analyze_writing_style(cover_letters)
        save_writing_analysis(user_id, analysis)
        
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-writing-analysis', methods=['GET'])
def get_writing_analysis_api():
    try:
        user_id = get_or_create_user()
        analysis = get_writing_analysis(user_id)
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-master-resume', methods=['POST'])
def upload_master_resume_api():
    try:
        user_id = get_or_create_user()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file.content_type == "application/pdf":
            content = extract_text_from_pdf(io.BytesIO(file.read()))
        else:
            content = file.read().decode("utf-8")
        
        if content:
            save_master_resume(user_id, content, file.filename)
            return jsonify({
                'message': f'Master resume uploaded successfully: {file.filename}',
                'filename': file.filename
            })
        else:
            return jsonify({'error': 'Could not extract content from file'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-master-resume', methods=['GET'])
def get_master_resume_api():
    try:
        user_id = get_or_create_user()
        master_resume = get_master_resume(user_id)
        return jsonify({'master_resume': master_resume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-resume', methods=['POST'])
def generate_resume_api():
    try:
        user_id = get_or_create_user()
        data = request.get_json()
        job_description = data.get('job_description', '')
        output_format = data.get('output_format', 'text')
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        # Get stored master resume
        master_resume = get_master_resume(user_id)
        if not master_resume:
            return jsonify({'error': 'No master resume found. Please upload your master resume first.'}), 400
        
        # Get stored writing style analysis
        writing_style = get_writing_analysis(user_id) or "No writing style analysis available."
        
        optimized_resume = generate_optimized_resume(master_resume, job_description, writing_style, output_format)
        return jsonify({'resume': optimized_resume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter_api():
    try:
        user_id = get_or_create_user()
        data = request.get_json()
        job_description = data.get('job_description', '')
        company_name = data.get('company_name', '')
        job_title = data.get('job_title', '')
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        # Get stored master resume
        master_resume = get_master_resume(user_id)
        if not master_resume:
            return jsonify({'error': 'No master resume found. Please upload your master resume first.'}), 400
        
        # Get stored writing style analysis
        writing_style = get_writing_analysis(user_id) or "No writing style analysis available."
        
        cover_letter = generate_cover_letter(master_resume, job_description, writing_style, company_name, job_title)
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

# For Vercel deployment
app.debug = True 