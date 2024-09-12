# PDF Study Assistant

PDF Study Assistant is a powerful, interactive tool that combines PDF viewing capabilities with AI-powered analysis, web search functionality, and advanced text recognition features. It's designed to enhance your study experience by providing intelligent assistance and easy access to information.

## Features

1. **PDF Viewing and Navigation**
   - Load PDFs by clicking the "Browse PDF" button or dragging and dropping files
   - Navigate through pages using "Previous Page" and "Next Page" buttons
   - Smooth scrolling and zooming capabilities

2. **Text Selection and Copying**
   - Select text from PDFs using a blue rectangle selection tool
   - Copy selected text to clipboard automatically
   - Works with both text-based and image-based (scanned) PDFs

3. **Optical Character Recognition (OCR)**
   - Extract text from images and scanned documents within PDFs
   - Recognize and copy text from photographs or handwritten notes

4. **AI-Powered Analysis**
   - Highlight text and submit it for AI analysis
   - Submit entire PDF pages for comprehensive AI review
   - Interact with an AI assistant for explanations, summaries, and insights

5. **Web Search Integration**
   - Perform web searches directly from the application
   - AI can initiate searches based on context and provide summarized results

6. **LaTeX Equation Recognition**
   - Convert images of mathematical equations to LaTeX expressions
   - Render LaTeX equations as images in the chat history

7. **Customizable Interface**
   - Toggle the AI chat panel visibility
   - Adjust font settings for the chat history

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/pdf-study-assistant.git
   cd pdf-study-assistant
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv environ
   source environ/bin/activate  # On Windows, use: environ\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR:
   - Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

5. Set up environment variables:
   Create a `.env` file in the project root and add your API keys:
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key
   SERPAPI_API_KEY=your_serpapi_api_key
   ```

6. Run the application:
   ```
   python main.py
   ```

## Usage and AI Interaction

1. **Loading a PDF**
   - Click "Browse PDF" or drag and drop a PDF file onto the application window

2. **Text Selection and Copying**
   - Click and drag to create a blue rectangle over the desired text
   - Text is automatically copied to clipboard upon release

3. **Highlighting for AI Analysis**
   - Click the "Highlight" button to enter highlight mode
   - Create an orange highlight over text or equations
   - Click "Submit Highlighted Text" to send for AI analysis

4. **Chatting with AI**
   - Type messages in the input field at the bottom of the AI panel
   - Use "/chat" command for general queries:
     ```
     /chat Explain the concept of quantum entanglement
     ```
   - Use "/search" command for web searches:
     ```
     /search Latest advancements in renewable energy
     ```

5. **Submitting PDF Content**
   - Click "Submit PDF to AI" to analyze the current page and last two pages

6. **LaTeX Equation Recognition**
   - Highlight an equation image and submit it for analysis
   - The AI will attempt to convert it to a LaTeX expression

7. **OCR for Scanned Documents**
   - Select text from scanned or image-based PDFs as you would with regular PDFs
   - The application will automatically use OCR to extract the text

## Tips for Best Results

- Ensure good lighting and image quality when working with scanned documents
- For equation recognition, try to highlight only the equation, minimizing surrounding text
- Use specific queries when interacting with the AI for more accurate responses

## Troubleshooting

- If OCR is not working, ensure Tesseract is properly installed and in your system PATH
- For LaTeX rendering issues, make sure you have a LaTeX distribution installed on your system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Hotmail.com. I'm going to show you how to do that. I'm going to show you.