# AI Resume Optimizer

An intelligent resume optimization tool that learns your writing style from cover letters and generates tailored resumes for specific job descriptions.

## 🔒 **Security Features**

### **Critical Security Implementations**
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Rate Limiting**: Prevents abuse with configurable limits per endpoint
- **Input Validation**: Comprehensive validation for all user inputs
- **File Upload Security**: Secure file handling with size and type restrictions
- **Security Headers**: XSS protection, content type options, frame options
- **Secure Session Management**: Proper session handling with secure cookies
- **Environment-based Configuration**: No hardcoded secrets

### **File Storage Security**
- **Secure File Storage**: Files stored in user-specific directories
- **File Type Validation**: Only PDF and TXT files allowed
- **File Size Limits**: Maximum 10MB per file
- **Filename Sanitization**: Prevents path traversal attacks
- **Temporary File Cleanup**: Automatic cleanup of temporary files

## 🚀 **Features**

### 🔐 **User Authentication System**
- **Secure login/signup** with email and password
- **Cross-device access** - Your data follows you across all devices
- **Persistent data storage** - No need to re-upload documents
- **Secure user isolation** - Each user's data is completely private
- **Session management** - Automatic login persistence
- **Rate limiting** - Prevents brute force attacks

### 🎯 **Persistent Writing Style Learning**
- Upload multiple cover letters to teach the AI your unique writing style
- **Automatic data persistence** - Your cover letters and writing analysis are saved permanently
- **Cross-device access** - Access your data from any device
- **No re-uploading needed** - Data persists across sessions and devices
- **User accounts** - Each user gets their own secure data storage
- Automatic analysis of tone, vocabulary, and personal voice
- Maintains consistency across all generated content

### 📄 **Master Resume System**
- Upload your complete resume with ALL experiences once
- AI intelligently edits and optimizes for each specific job
- **Cross-device access** - Your master resume is available everywhere
- **Smart editing** - Keeps relevant experiences, removes/minimizes irrelevant ones
- **Cost efficient** - Uses stored master resume instead of re-uploading
- Includes keywords from the job description

### 🎨 **Multiple Output Formats**
- **LaTeX**: Clean LaTeX code without preamble (token-efficient)
- **Text**: Plain text version for easy editing

### 💼 **Job-Specific Tailoring**
- Analyzes job descriptions for requirements and keywords
- Optimizes content to match the target role
- Ensures one-page format with impactful content

### 💰 **Cost Optimization**
- **Cached writing analysis** - No repeated API calls for analysis
- **Stored context** - Reduces token usage for returning users
- **Smart caching** - 60-80% cost reduction for returning users

### 🎨 **Enhanced UI/UX**
- **Loading Animations**: Beautiful loading overlays for all operations
- **Progress Indicators**: Real-time upload progress with visual feedback
- **Error Handling**: User-friendly error messages and validation
- **Responsive Design**: Works perfectly on all devices
- **Modern Interface**: Clean, professional design with smooth animations

## 🛠️ **Installation**

### **Prerequisites**
- Python 3.12+
- OpenAI API key
- Git

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd JobOptimizer
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Set Up Environment Variables**
Create a `.env` file in the project root:
```env
# Required for security
SECRET_KEY=your_very_long_random_secret_key_here

# Required for AI functionality
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Database URL for production (Supabase)
DATABASE_URL=your_supabase_database_url_here

# Optional: Flask configuration
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

**Important**: Generate a strong SECRET_KEY:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### **4. Initialize Database**
```bash
python init_db.py
```

### **5. Test the Application**
```bash
python test_app.py
```

## 🚀 **Usage**

### **Local Development**

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Open your browser:**
   Visit `http://localhost:5000`

3. **Create an account:**
   - Click "Sign up" to create your account
   - Use your email and a secure password
   - Your data will be securely stored

### **Web Interface Guide**

1. **Account Setup (One-time):**
   - Create an account with your email and password
   - Log in to access your personalized dashboard
   - Your data is securely stored and accessible from any device

2. **Upload Master Resume (One-time setup):**
   - Upload your complete resume with ALL your experiences
   - **Your master resume is automatically saved** and accessible from any device
   - Include everything - the AI will intelligently edit for each job
   - **Supported formats**: PDF, TXT (max 10MB)

3. **Upload Cover Letters (One-time setup):**
   - Use the file upload area to upload multiple cover letters
   - **Your cover letters are automatically saved** and accessible from any device
   - Click "Analyze Writing Style" to learn your writing patterns
   - **No need to re-upload** - Your data is stored securely
   - This helps maintain your unique voice in generated resumes
   - **Supported formats**: PDF, TXT (max 10MB each)

4. **Generate Optimized Content:**
   - Simply paste the job description
   - The AI will automatically use your stored master resume and writing style
   - Generate optimized resumes and cover letters instantly

5. **Add Job Description:**
   - Paste the complete job description you're targeting
   - Include requirements, responsibilities, and qualifications

6. **Choose Output Format:**
   - **LaTeX**: Returns clean LaTeX code (minimal tokens)
   - **Text**: Plain text version

7. **Generate Optimized Content:**
   - Click "Generate Optimized Resume" or "Cover Letter"
   - Watch the beautiful loading animations
   - Review and copy the results

### **Cross-Device Benefits**

- **Access from anywhere** - Log in from any device to access your data
- **No re-uploading** - Your documents are stored securely in your account
- **Consistent experience** - Same interface and data across all devices
- **Secure storage** - Your data is protected and isolated from other users

### **Output Formats Explained**

#### LaTeX Format
- Returns only the content portion (no preamble)
- Token-efficient for API usage
- Copy the code into your existing LaTeX document
- Professional formatting with proper structure

#### Text Format
- Plain text version
- Easy to copy and paste
- Good for further editing

## 🔧 **Technical Details**

### **Security Architecture**
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Rate Limiting**: Flask-Limiter with configurable limits
- **Input Validation**: Comprehensive validation for all inputs
- **File Security**: Secure file upload with validation and sanitization
- **Session Security**: Secure session management with proper headers
- **Error Handling**: Secure error handling without information leakage

### **Database Architecture**
- **Dual Database Support**: SQLite for development, PostgreSQL for production
- **User Isolation**: Complete data separation between users
- **File Storage**: Secure file storage with user-specific directories
- **Data Persistence**: All user data persists across sessions

### **File Storage Strategy**
- **User-specific directories**: Each user gets their own upload folder
- **Secure filenames**: Sanitized filenames prevent path traversal
- **File validation**: Type and size validation before processing
- **Automatic cleanup**: Temporary files are cleaned up automatically

### **User Authentication**
- **Secure password hashing** using Werkzeug
- **Session management** with Flask-Login
- **Database isolation** - Each user's data is completely separate
- **Cross-device sessions** - Login persists across devices
- **Rate limiting** - Prevents brute force attacks

### **Writing Style Analysis**
The system analyzes your cover letters to understand:
- Writing tone and formality level
- Sentence structure and complexity
- Vocabulary and technical terminology
- Personal voice characteristics
- Achievement description patterns

### **Resume Optimization Process**
1. **Content Analysis**: Extracts key information from your resume
2. **Job Matching**: Identifies relevant requirements and keywords
3. **Style Application**: Applies your learned writing style
4. **Content Generation**: Creates optimized, job-specific content
5. **Formatting**: Structures content for the chosen output format

### **Cost Optimization Features**
- **Cached writing analysis** - Analyzed once, used forever
- **Stored context** - Reduces API calls for returning users
- **Smart data reuse** - 60-80% cost reduction for returning users

## 📋 **Requirements**

- Python 3.12+
- OpenAI API key
- Flask for web interface
- SQLite (included with Python) or PostgreSQL

## 📦 **Dependencies**

- `flask`: Web interface
- `flask-login`: User authentication
- `flask-wtf`: CSRF protection and form handling
- `flask-limiter`: Rate limiting
- `werkzeug`: Password hashing and utilities
- `openai`: AI API integration
- `PyPDF2`: PDF text extraction
- `python-dotenv`: Environment variable management
- `psycopg2-binary`: PostgreSQL support (production)

## 🧪 **Testing**

Run the test script to verify everything is working:
```bash
python test_app.py
```

## 🚀 **Deployment**

### **Local Development**
```bash
python app.py
```

### **Production (Vercel)**
The application is configured for Vercel deployment with `vercel.json`.

### **Environment Variables for Production**
- `SECRET_KEY`: Strong random secret key
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string (optional)
- `FLASK_DEBUG`: Set to `False` in production

## 💡 **Tips for Best Results**

1. **Create an account** - Secure your data and enable cross-device access
2. **Upload Multiple Cover Letters**: More samples = better style learning
3. **Provide Complete Job Descriptions**: Include all requirements and responsibilities
4. **Use LaTeX Format**: Most token-efficient option
5. **Review Generated Content**: Always review and edit as needed
6. **Keep Resumes Updated**: Upload your most current resume
7. **Log in from any device** - Your data follows you everywhere
8. **Use strong passwords** - Protect your account with secure passwords

## 🔒 **Security Notes**

- **Never commit your .env file** - It contains sensitive information
- **Use strong SECRET_KEY** - Generate a random 32+ character key
- **Keep your OpenAI API key secure** - Don't share it publicly
- **Regular updates** - Keep dependencies updated for security patches
- **Monitor logs** - Check application logs for suspicious activity

## 🐛 **Troubleshooting**

### **Common Issues**

1. **"SECRET_KEY environment variable is not set"**
   - Create a `.env` file with a strong SECRET_KEY
   - Generate one using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **"OpenAI API key not configured"**
   - Add your OpenAI API key to the `.env` file
   - Get one from https://platform.openai.com/api-keys

3. **Upload fails**
   - Check file size (max 10MB)
   - Ensure file is PDF or TXT format
   - Check uploads directory permissions

4. **Database errors**
   - Run `python init_db.py` to initialize the database
   - Check database file permissions

### **Getting Help**

1. Run `python test_app.py` to check your setup
2. Check the application logs for error messages
3. Ensure all environment variables are set correctly
4. Verify all dependencies are installed: `pip install -r requirements.txt`

## Contributing

Feel free to submit issues and enhancement requests!

## License

[Add your license information here]
