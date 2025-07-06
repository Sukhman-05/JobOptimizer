# AI Resume Optimizer

An intelligent resume optimization tool that learns your writing style from cover letters and generates tailored resumes for specific job descriptions.

## Features

### 🔐 **User Authentication System**
- **Secure login/signup** with email and password
- **Cross-device access** - Your data follows you across all devices
- **Persistent data storage** - No need to re-upload documents
- **Secure user isolation** - Each user's data is completely private
- **Session management** - Automatic login persistence

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

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd JobOptimizer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```
   
   Or add to `pyproject.toml`:
   ```toml
   [tool.resume-reviewer]
   openai_api_key = "your_openai_api_key_here"
   secret_key = "your_secret_key_here"
   ```

## Usage

### Local Development

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

### Web Interface Guide

1. **Account Setup (One-time):**
   - Create an account with your email and password
   - Log in to access your personalized dashboard
   - Your data is securely stored and accessible from any device

2. **Upload Master Resume (One-time setup):**
   - Upload your complete resume with ALL your experiences
   - **Your master resume is automatically saved** and accessible from any device
   - Include everything - the AI will intelligently edit for each job

3. **Upload Cover Letters (One-time setup):**
   - Use the file upload area to upload multiple cover letters
   - **Your cover letters are automatically saved** and accessible from any device
   - Click "Analyze Writing Style" to learn your writing patterns
   - **No need to re-upload** - Your data is stored securely
   - This helps maintain your unique voice in generated resumes

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
   - Review and copy the results

### Cross-Device Benefits

- **Access from anywhere** - Log in from any device to access your data
- **No re-uploading** - Your documents are stored securely in your account
- **Consistent experience** - Same interface and data across all devices
- **Secure storage** - Your data is protected and isolated from other users

### Output Formats Explained

#### LaTeX Format
- Returns only the content portion (no preamble)
- Token-efficient for API usage
- Copy the code into your existing LaTeX document
- Professional formatting with proper structure

#### Text Format
- Plain text version
- Easy to copy and paste
- Good for further editing

## Technical Details

### User Authentication
- **Secure password hashing** using Werkzeug
- **Session management** with Flask-Login
- **Database isolation** - Each user's data is completely separate
- **Cross-device sessions** - Login persists across devices

### Writing Style Analysis
The system analyzes your cover letters to understand:
- Writing tone and formality level
- Sentence structure and complexity
- Vocabulary and technical terminology
- Personal voice characteristics
- Achievement description patterns

### Resume Optimization Process
1. **Content Analysis**: Extracts key information from your resume
2. **Job Matching**: Identifies relevant requirements and keywords
3. **Style Application**: Applies your learned writing style
4. **Content Generation**: Creates optimized, job-specific content
5. **Formatting**: Structures content for the chosen output format

### Cost Optimization Features
- **Cached writing analysis** - Analyzed once, used forever
- **Stored context** - Reduces API calls for returning users
- **Smart data reuse** - 60-80% cost reduction for returning users

## Requirements

- Python 3.12+
- OpenAI API key
- Flask for web interface
- SQLite (included with Python)

## Dependencies

- `flask`: Web interface
- `flask-login`: User authentication
- `flask-wtf`: Form handling
- `werkzeug`: Password hashing and utilities
- `openai`: AI API integration
- `PyPDF2`: PDF text extraction
- `python-dotenv`: Environment variable management
- `sqlite3`: Database storage (built-in)

## Tips for Best Results

1. **Create an account** - Secure your data and enable cross-device access
2. **Upload Multiple Cover Letters**: More samples = better style learning
3. **Provide Complete Job Descriptions**: Include all requirements and responsibilities
4. **Use LaTeX Format**: Most token-efficient option
5. **Review Generated Content**: Always review and edit as needed
6. **Keep Resumes Updated**: Upload your most current resume
7. **Log in from any device** - Your data follows you everywhere

## Troubleshooting

### Authentication Issues
- Ensure you're using the correct email and password
- Check that your account was created successfully
- Clear browser cookies if login issues persist

### API Issues
- Verify your OpenAI API key is valid
- Check your API usage limits
- Ensure stable internet connection

### File Upload Issues
- Use PDF or TXT formats only
- Ensure files are not corrupted
- Check file size limits

### Deployment Issues
- Check Vercel build logs for errors
- Verify environment variables are set correctly
- Ensure all dependencies are in `requirements.txt`

## Contributing

Feel free to submit issues and enhancement requests!

## License

[Add your license information here]
