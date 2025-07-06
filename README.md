# AI Resume Optimizer

An intelligent resume optimization tool that learns your writing style from cover letters and generates tailored resumes for specific job descriptions.

## Features

### 🎯 **Writing Style Learning**
- Upload multiple cover letters to teach the AI your unique writing style
- Automatic analysis of tone, vocabulary, and personal voice
- Maintains consistency across all generated content

### 📄 **Smart Resume Optimization**
- Analyzes your current resume and target job description
- Generates optimized content that matches the job requirements
- Focuses on relevant achievements and skills
- Includes keywords from the job description

### 🎨 **Multiple Output Formats**
- **LaTeX**: Clean LaTeX code without preamble (token-efficient)
- **Text**: Plain text version for easy editing

### 💼 **Job-Specific Tailoring**
- Analyzes job descriptions for requirements and keywords
- Optimizes content to match the target role
- Ensures one-page format with impactful content

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
   ```
   
   Or add to `pyproject.toml`:
   ```toml
   [tool.resume-reviewer]
   openai_api_key = "your_openai_api_key_here"
   ```

## Usage

### Local Development

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Open your browser:**
   Visit `http://localhost:5000`

### Web Interface Guide

1. **Upload Cover Letters (Optional but Recommended):**
   - Use the file upload area to upload multiple cover letters
   - Click "Analyze Writing Style" to learn your writing patterns
   - This helps maintain your unique voice in generated resumes

2. **Upload Your Resume:**
   - Upload your current resume in PDF or TXT format
   - The system will extract and display the content

3. **Add Job Description:**
   - Paste the complete job description you're targeting
   - Include requirements, responsibilities, and qualifications

4. **Choose Output Format:**
   - **LaTeX**: Returns clean LaTeX code (minimal tokens)
   - **Text**: Plain text version

5. **Generate Optimized Resume:**
   - Click "Generate Optimized Resume" or "Cover Letter"
   - Review and copy the results

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

## Deployment

### Vercel Deployment (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Add environment variable: `OPENAI_API_KEY`
   - Deploy!

3. **Your app will be live at:** `https://your-project-name.vercel.app`

## Technical Details

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

## Requirements

- Python 3.12+
- OpenAI API key
- Flask for web interface

## Dependencies

- `flask`: Web interface
- `openai`: AI API integration
- `PyPDF2`: PDF text extraction
- `python-dotenv`: Environment variable management
- `pathlib`: File path handling

## Tips for Best Results

1. **Upload Multiple Cover Letters**: More samples = better style learning
2. **Provide Complete Job Descriptions**: Include all requirements and responsibilities
3. **Use LaTeX Format**: Most token-efficient option
4. **Review Generated Content**: Always review and edit as needed
5. **Keep Resumes Updated**: Upload your most current resume

## Troubleshooting

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
