# Document Compare Intelligence

A powerful Streamlit application that uses Google's Gemini AI to compare and visualize differences between PDF documents.

## Overview

Document Compare Intelligence allows you to upload two PDF documents and quickly identify all changes between them. The application:

1. Extracts text from both PDFs
2. Uses Google's Gemini AI to analyze and identify differences
3. Generates a comprehensive summary of changes
4. Provides a color-coded visualization of additions, deletions, and modifications

This tool is perfect for:
- Contract review and change tracking
- Document version comparison
- Legal document analysis
- Content revision management

## Features

- **PDF Text Extraction**: Robust extraction using multiple methods (pdfplumber and PyPDF2)
- **Intelligent Difference Analysis**: AI-powered identification of meaningful changes
- **Change Visualization**: Color-coded display showing:
  - Additions (green)
  - Deletions (red, strikethrough)
  - Modifications (yellow, with tooltip showing original text)
  - Unchanged text (normal)
- **Change Summary**: Concise overview of document modifications
- **Detailed Analysis**: In-depth explanation of significant changes

## Requirements

- Python 3.7+
- Streamlit
- PyPDF2
- pdfplumber
- Google Generative AI Python SDK
- dotenv

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/nageswarao7/document-compare-intelligence.git
   cd document-compare-intelligence
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your Google API key:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

## Usage

1. Start the application:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL shown in your terminal (typically http://localhost:8501)

3. Upload two PDF documents:
   - The original document in the left panel
   - The modified document in the right panel

4. Click "Compare Documents" to start the analysis

5. Review the results:
   - Summary of changes
   - Detailed analysis
   - Color-coded visualization of differences

## Project Structure

```
document-compare-intelligence/
├── app.py                # Main Streamlit application
├── pdf_processor.py      # PDF text extraction functions
├── llm_comparer.py       # Gemini AI integration for text comparison
├── visualizer.py         # HTML generation for visualizing differences
├── requirements.txt      # Project dependencies
├── .env                  # Environment variables (API keys)
└── README.md             # Project documentation
```

## Configuration

You can adjust the following parameters in the code:

- `max_chunk_size`: Maximum text chunk size for processing (default: 8000)
- Model selection: Change the Gemini model (default: "gemini-2.5-pro-preview-03-25")
- Temperature settings for AI responses

## Troubleshooting

**Error: "Google API key not found"**
- Ensure you have created a `.env` file with your Google API key

**Poor text extraction results**
- The application uses two different PDF extraction methods. If one fails, try with different PDF files or pre-process the PDFs to ensure text is properly embedded.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

## Acknowledgments

- This project uses Google's Gemini AI for intelligent text comparison
- Built with Streamlit for a simple and intuitive user interface
