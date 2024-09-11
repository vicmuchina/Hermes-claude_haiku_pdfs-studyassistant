# PDF Study Assistant

PDF Study Assistant is an interactive tool that combines PDF viewing capabilities with AI-powered analysis and web search functionality.

## Features

- Load a PDF by clicking the "Browse PDF" button or dragging and dropping a file onto the application window.
- Use the toolbar buttons to navigate pages, highlight text, and interact with the AI assistant.
- To chat with the DuckDuckGo AI, start your message with "/chat" followed by your query.
- To perform a web search, start your message with "/search" followed by your query.
- LaTeX equations in AI responses will be automatically rendered as images in the chat history.
- Use the font selection dropdown in the toolbar to customize the chat history font.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/vicmuchina/Hermes-claude_haiku_pdfs-studyassistant
   ```

2. Navigate to the project directory:
   ```
   cd pdf-study-assistant
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python main.py
   ```

## AI Interaction Examples

1. Chat with DuckDuckGo AI:
   ```
   /chat Explain the concept of quantum entanglement
   ```

2. Perform a web search:
   ```
   /search Latest advancements in renewable energy
   ```

3. Analyze highlighted text:
   Highlight a portion of the PDF text and click "Submit Highlighted Text" to get AI analysis.

4. Submit PDF for analysis:
   Click "Submit PDF to AI" to get an analysis of the current page and the last two pages of the document.

## Future Improvements

1. Integration with additional AI models and services
2. Automatic summarization of PDF content
3. Question generation for self-testing
4. Multi-language support and translation features
5. Citation generation for academic use
6. Integration with note-taking applications
7. Collaborative study features for group learning
8. Enhanced LaTeX rendering options and customization

## Contributing

Contributions are welcome and encouraged! If you'd like to contribute to this project, please feel free to submit a Pull Request or open an Issue for discussion. We're open to collaboration and always looking for ways to improve the PDF Study Assistant.
