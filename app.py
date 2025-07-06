from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import PyPDF2
import io
import os
import json
import re
import logging
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import subprocess
import tempfile
import tomllib
import base64
import uuid
import hashlib
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import execute_query, execute_query_with_return, execute_query_single, init_database

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    logger.error("SECRET_KEY environment variable is not set!")
    raise ValueError("SECRET_KEY environment variable must be set for security")

app.secret_key = SECRET_KEY

# CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# File Upload Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file):
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    return size <= MAX_FILE_SIZE

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Security Headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = execute_query_single('SELECT id, email FROM users WHERE id = %s', (user_id,))
    if user_data:
        return User(user_data[0], user_data[1])
    return None

# Database setup - now handled by database.py
def init_db():
    init_database()

# Initialize database
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"⚠️ Database initialization warning: {e}")

# Load API key from environment variable only
def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("Warning: OPENAI_API_KEY environment variable not set")
        return None
    return api_key

OPENAI_API_KEY = get_openai_api_key()

# Input validation functions
def validate_email(email):
    """Validate email format"""
    if not email or '@' not in email or '.' not in email:
        return False
    return True

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 6:
        return False
    return True

def sanitize_filename(filename):
    """Sanitize filename for security"""
    if not filename:
        return None
    # Remove any path components and sanitize
    filename = os.path.basename(filename)
    # Only allow alphanumeric, dots, hyphens, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename

# Authentication functions
def register_user(email, password):
    """Register a new user with validation"""
    try:
        if not validate_email(email):
            return None, "Invalid email format"
        
        if not validate_password(password):
            return None, "Password must be at least 6 characters long"
        
        password_hash = generate_password_hash(password)
        user_id = execute_query_with_return(
            'INSERT INTO users (email, password_hash) VALUES (%s, %s)',
            (email, password_hash)
        )
        return user_id, None
    except Exception as e:
        logger.error(f"Registration error: {e}")
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return None, "Email already registered"
        return None, "Registration failed"

def authenticate_user(email, password):
    """Authenticate a user with validation"""
    if not validate_email(email):
        return None
    
    user_data = execute_query_single('SELECT id, email, password_hash FROM users WHERE email = %s', (email,))
    
    if user_data and check_password_hash(user_data[2], password):
        # Update last login
        execute_query('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user_data[0],))
        return User(user_data[0], user_data[1])
    return None

# File storage functions
def save_file_to_storage(file, user_id, file_type):
    """Save file to storage and return file path"""
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    if not validate_file_size(file):
        raise ValueError("File too large (max 10MB)")
    
    # Create user-specific directory
    user_dir = os.path.join(UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    filename = sanitize_filename(file.filename)
    if not filename:
        filename = f"file_{uuid.uuid4().hex}"
    
    # Add timestamp to prevent conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    safe_filename = f"{name}_{timestamp}{ext}"
    
    file_path = os.path.join(user_dir, safe_filename)
    
    # Save file
    file.save(file_path)
    
    return file_path, safe_filename

def extract_text_from_file(file_path):
    """Extract text from file based on type"""
    try:
        if file_path.lower().endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
    except Exception as e:
        logger.error(f"Error extracting text from file: {e}")
        raise ValueError(f"Error reading file: {str(e)}")

# Data management functions
def save_cover_letter(user_id, content, filename, file_path=None):
    """Save cover letter to database"""
    execute_query(
        'INSERT INTO cover_letters (user_id, content, filename, file_path) VALUES (%s, %s, %s, %s)',
        (user_id, content, filename, file_path)
    )

def get_user_cover_letters(user_id):
    """Get all cover letters for a user"""
    results = execute_query('SELECT content FROM cover_letters WHERE user_id = %s', (user_id,))
    if results:
        return [row[0] for row in results]
    return []

def save_writing_analysis(user_id, analysis):
    """Save writing style analysis to database"""
    # First try to delete existing record, then insert new one
    execute_query('DELETE FROM writing_analysis WHERE user_id = %s', (user_id,))
    execute_query('''
        INSERT INTO writing_analysis (user_id, analysis, updated_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
    ''', (user_id, analysis))

def get_writing_analysis(user_id):
    """Get writing style analysis for a user"""
    result = execute_query_single(
        'SELECT analysis FROM writing_analysis WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1',
        (user_id,)
    )
    return result[0] if result else None

def save_master_resume(user_id, content, filename, file_path=None):
    """Save master resume to database"""
    # First try to delete existing record, then insert new one
    execute_query('DELETE FROM master_resume WHERE user_id = %s', (user_id,))
    execute_query('''
        INSERT INTO master_resume (user_id, content, filename, file_path)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, content, filename, file_path))

def get_master_resume(user_id):
    """Get master resume for a user"""
    result = execute_query_single(
        'SELECT content FROM master_resume WHERE user_id = %s ORDER BY uploaded_at DESC LIMIT 1',
        (user_id,)
    )
    return result[0] if result else None

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
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('login.html')
        
        user = authenticate_user(email, password)
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
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
@limiter.limit("10 per minute")
def upload_cover_letters_api():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        uploaded_count = 0
        errors = []
        
        for file in files:
            if file and file.filename:
                try:
                    # Validate file
                    if not allowed_file(file.filename):
                        errors.append(f"Invalid file type for {file.filename}")
                        continue
                    
                    if not validate_file_size(file):
                        errors.append(f"File too large for {file.filename}")
                        continue
                    
                    # Save file to storage
                    file_path, safe_filename = save_file_to_storage(file, current_user.id, 'cover_letter')
                    
                    # Extract text from file
                    content = extract_text_from_file(file_path)
                    
                    # Save to database
                    save_cover_letter(current_user.id, content, safe_filename, file_path)
                    uploaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {e}")
                    errors.append(f"Error processing {file.filename}: {str(e)}")
        
        response = {'message': f'Successfully uploaded {uploaded_count} cover letter(s)'}
        if errors:
            response['warnings'] = errors
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/api/get-cover-letters', methods=['GET'])
@login_required
def get_cover_letters_api():
    try:
        cover_letters = get_user_cover_letters(current_user.id)
        return jsonify({'cover_letters': cover_letters})
    except Exception as e:
        logger.error(f"Error getting cover letters: {e}")
        return jsonify({'error': 'Failed to retrieve cover letters'}), 500

@app.route('/api/analyze-writing-style', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def analyze_writing_style_api():
    try:
        cover_letters = get_user_cover_letters(current_user.id)
        
        if not cover_letters:
            return jsonify({'error': 'No cover letters found. Please upload some cover letters first.'}), 400
        
        analysis = analyze_writing_style(cover_letters)
        save_writing_analysis(current_user.id, analysis)
        return jsonify({'analysis': analysis})
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': 'Analysis failed'}), 500

@app.route('/api/get-writing-analysis', methods=['GET'])
@login_required
def get_writing_analysis_api():
    try:
        analysis = get_writing_analysis(current_user.id)
        return jsonify({'analysis': analysis})
    except Exception as e:
        logger.error(f"Error getting writing analysis: {e}")
        return jsonify({'error': 'Failed to retrieve analysis'}), 500

@app.route('/api/upload-master-resume', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def upload_master_resume_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF and TXT files are allowed.'}), 400
        
        if not validate_file_size(file):
            return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 400
        
        # Save file to storage
        file_path, safe_filename = save_file_to_storage(file, current_user.id, 'resume')
        
        # Extract text from file
        content = extract_text_from_file(file_path)
        
        # Save to database
        save_master_resume(current_user.id, content, safe_filename, file_path)
        
        return jsonify({'message': 'Master resume uploaded successfully'})
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/get-master-resume', methods=['GET'])
@login_required
def get_master_resume_api():
    try:
        master_resume = get_master_resume(current_user.id)
        return jsonify({'master_resume': master_resume})
    except Exception as e:
        logger.error(f"Error getting master resume: {e}")
        return jsonify({'error': 'Failed to retrieve master resume'}), 500

@app.route('/api/generate-resume', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def generate_resume_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        job_description = data.get('job_description', '').strip()
        output_format = data.get('output_format', 'text')
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        master_resume = get_master_resume(current_user.id)
        if not master_resume:
            return jsonify({'error': 'Please upload a master resume first'}), 400
        
        writing_style = get_writing_analysis(current_user.id)
        if not writing_style:
            return jsonify({'error': 'Please analyze your writing style first'}), 400
        
        resume = generate_optimized_resume(master_resume, job_description, writing_style, output_format)
        return jsonify({'resume': resume})
    except Exception as e:
        logger.error(f"Resume generation error: {e}")
        return jsonify({'error': 'Resume generation failed'}), 500

@app.route('/api/generate-cover-letter', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def generate_cover_letter_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        job_description = data.get('job_description', '').strip()
        company_name = data.get('company_name', '').strip()
        job_title = data.get('job_title', '').strip()
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        master_resume = get_master_resume(current_user.id)
        if not master_resume:
            return jsonify({'error': 'Please upload a master resume first'}), 400
        
        writing_style = get_writing_analysis(current_user.id)
        if not writing_style:
            return jsonify({'error': 'Please analyze your writing style first'}), 400
        
        cover_letter = generate_cover_letter(master_resume, job_description, writing_style, company_name, job_title)
        return jsonify({'cover_letter': cover_letter})
    except Exception as e:
        logger.error(f"Cover letter generation error: {e}")
        return jsonify({'error': 'Cover letter generation failed'}), 500

@app.route('/api/extract-text', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def extract_text_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF and TXT files are allowed.'}), 400
        
        if not validate_file_size(file):
            return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 400
        
        # Save file temporarily
        file_path, safe_filename = save_file_to_storage(file, current_user.id, 'temp')
        
        # Extract text
        content = extract_text_from_file(file_path)
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify({'text': content})
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        return jsonify({'error': f'Error extracting text: {str(e)}'}), 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

if __name__ == '__main__':
    # Environment-based configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port) 