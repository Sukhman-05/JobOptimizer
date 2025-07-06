from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, email FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1])
    return None

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table with authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_sessions table for session management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create cover_letters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create writing_analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS writing_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            analysis TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create master_resume table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_resume (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Load API key from environment variable only
def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set")
        return None
    return api_key

OPENAI_API_KEY = get_openai_api_key()

# Authentication functions
def register_user(email, password):
    """Register a new user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "Email already registered"
    except Exception as e:
        conn.close()
        return None, str(e)

def authenticate_user(email, password):
    """Authenticate a user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, password_hash FROM users WHERE email = ?', (email,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data and check_password_hash(user_data[2], password):
        # Update last login
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_data[0],))
        conn.commit()
        conn.close()
        return User(user_data[0], user_data[1])
    return None

# Data management functions
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

    User's Writing Style Analysis:
    {writing_style}

    Generate an optimized resume that:
    1. Uses ONLY information from the master resume
    2. Matches the user's writing style and tone
    3. Optimizes for the specific job description
    4. Maintains all factual information
    5. Focuses on relevant achievements and skills"""

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
    """Generate a cover letter based on the user's writing style and resume"""
    
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""Create a compelling cover letter for this job application:

    User's Resume Content:
    {master_resume_content}

    Target Job Description:
    {job_description}

    User's Writing Style Analysis:
    {writing_style}

    Company Name: {company_name}
    Job Title: {job_title}

    Generate a cover letter that:
    1. Matches the user's writing style and tone
    2. Highlights relevant experience from their resume
    3. Addresses the specific job requirements
    4. Shows enthusiasm for the role
    5. Maintains consistency with their writing personality
    6. Is professional and compelling"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert cover letter writer. Create compelling, personalized cover letters that match the user's writing style."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = authenticate_user(email, password)
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('signup.html')
        
        user_id, error = register_user(email, password)
        if user_id:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(str(error) if error else 'Registration failed', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# API Routes
@app.route('/api/upload-cover-letters', methods=['POST'])
@login_required
def upload_cover_letters_api():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_count = 0
    for file in files:
        if file and file.filename:
            try:
                if file.filename and file.filename.lower().endswith('.pdf'):
                    content = extract_text_from_pdf(file)
                else:
                    content = file.read().decode('utf-8')
                
                save_cover_letter(current_user.id, content, secure_filename(file.filename or 'unknown'))
                uploaded_count += 1
            except Exception as e:
                return jsonify({'error': f'Error processing {file.filename or "unknown"}: {str(e)}'}), 500
    
    return jsonify({'message': f'Successfully uploaded {uploaded_count} cover letter(s)'})

@app.route('/api/get-cover-letters', methods=['GET'])
@login_required
def get_cover_letters_api():
    cover_letters = get_user_cover_letters(current_user.id)
    return jsonify({'cover_letters': cover_letters})

@app.route('/api/analyze-writing-style', methods=['POST'])
@login_required
def analyze_writing_style_api():
    cover_letters = get_user_cover_letters(current_user.id)
    
    if not cover_letters:
        return jsonify({'error': 'No cover letters found. Please upload some cover letters first.'}), 400
    
    try:
        analysis = analyze_writing_style(cover_letters)
        save_writing_analysis(current_user.id, analysis)
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-writing-analysis', methods=['GET'])
@login_required
def get_writing_analysis_api():
    analysis = get_writing_analysis(current_user.id)
    return jsonify({'analysis': analysis})

@app.route('/api/upload-master-resume', methods=['POST'])
@login_required
def upload_master_resume_api():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        if file.filename and file.filename.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file)
        else:
            content = file.read().decode('utf-8')
        
        save_master_resume(current_user.id, content, secure_filename(file.filename or 'unknown'))
        return jsonify({'message': 'Master resume uploaded successfully'})
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/get-master-resume', methods=['GET'])
@login_required
def get_master_resume_api():
    master_resume = get_master_resume(current_user.id)
    return jsonify({'master_resume': master_resume})

@app.route('/api/generate-resume', methods=['POST'])
@login_required
def generate_resume_api():
    data = request.get_json()
    job_description = data.get('job_description', '')
    output_format = data.get('output_format', 'text')
    
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400
    
    master_resume = get_master_resume(current_user.id)
    if not master_resume:
        return jsonify({'error': 'Please upload a master resume first'}), 400
    
    writing_style = get_writing_analysis(current_user.id)
    if not writing_style:
        return jsonify({'error': 'Please analyze your writing style first'}), 400
    
    try:
        resume = generate_optimized_resume(master_resume, job_description, writing_style, output_format)
        return jsonify({'resume': resume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-cover-letter', methods=['POST'])
@login_required
def generate_cover_letter_api():
    data = request.get_json()
    job_description = data.get('job_description', '')
    company_name = data.get('company_name', '')
    job_title = data.get('job_title', '')
    
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400
    
    master_resume = get_master_resume(current_user.id)
    if not master_resume:
        return jsonify({'error': 'Please upload a master resume first'}), 400
    
    writing_style = get_writing_analysis(current_user.id)
    if not writing_style:
        return jsonify({'error': 'Please analyze your writing style first'}), 400
    
    try:
        cover_letter = generate_cover_letter(master_resume, job_description, writing_style, company_name, job_title)
        return jsonify({'cover_letter': cover_letter})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-text', methods=['POST'])
@login_required
def extract_text_api():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        if file.filename and file.filename.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file)
        else:
            content = file.read().decode('utf-8')
        
        return jsonify({'text': content})
    except Exception as e:
        return jsonify({'error': f'Error extracting text: {str(e)}'}), 500

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 