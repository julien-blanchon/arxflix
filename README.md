
![ArXFlix](./assets/image/llama6.png)

# ArXFlix

[![Arxflix - Youtube](https://img.shields.io/badge/Arxflix-Youtube-red)](https://www.youtube.com/@Arxflix)
[![Arxflix - X](https://img.shields.io/badge/Arxflix-X-black)](https://x.com/arxflix)

ArXFlix is a powerful tool that automatically transforms research papers from ArXiv into engaging two-minute video summaries. It leverages advanced AI models to extract key information, generate concise scripts, synthesize audio, and produce visually appealing videos complete with subtitles and rich content.

## Features

-   **Automated Paper Summarization:**
    -   Fetches paper content from ArXiv using either `arxiv_gpt` or `arxiv_html` methods.
    -   Generates concise summaries using AI models like OpenAI, Gemini, or local models.
-   **Script Generation:**
    -   Creates engaging video scripts tailored for a two-minute format.
    -   Supports multiple script generation methods: `openai`, `local`, and `gemini`.
-   **Audio Synthesis:**
    -   Converts scripts into natural-sounding audio using either `elevenlabs` or `lmnt` text-to-speech services.
-   **Video Generation:**
    -   Combines generated audio, subtitles (SRT), and rich content (JSON) to create a complete video.
    -   Uses FFmpeg for video processing.
-   **Flexible API:**
    -   Provides a FastAPI backend with endpoints for each stage of the video generation pipeline.
    -   Allows customization of AI models, audio services, and output formats.
-   **User-Friendly Frontend:**
    -   Offers a React-based frontend built with Next.js and Tailwind CSS.
    -   Provides an intuitive interface for users to input ArXiv paper IDs and generate videos.
-   **Gradio Demo:**
    -   Includes a Gradio demo (`arxflix_gradio.py`) for easy experimentation and sharing.

## Example Videos

[![Your Transformer Might Be Linear!](https://img.youtube.com/vi/FqGK-FDztgg/default.jpg)](https://youtu.be/FqGK-FDztgg)
[![Florence 2: The Future of Unified Vision Tasks!](https://img.youtube.com/vi/umc-jUMqrmE/default.jpg)](https://youtu.be/umc-jUMqrmE)
[![Kandinsky: Revolutionizing Text to Image Synthesis with Prior Models & Latent Diffusion](https://img.youtube.com/vi/1HptxaIGywk/default.jpg)](https://youtu.be/1HptxaIGywk)

## Installation and Usage

### Prerequisites

-   **Backend:**
    -   Python 3.9+
    -   FFmpeg
    -   pnpm
-   **Frontend:**
    -   Node.js
    -   pnpm

### Backend Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/julien-blanchon/arxflix.git
    cd arxflix/backend
    ```

2. **Create and activate a virtual environment (recommended):**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate  # Windows
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Install FFmpeg and pnpm (if not already installed):**

    ```bash
    # macOS
    brew install ffmpeg pnpm

    # Debian/Ubuntu (adjust for your distribution)
    sudo apt-get install ffmpeg pnpm
    ```

5. **Run the backend server:**

    ```bash
    uvicorn main:api --reload
    ```

    The backend server will be running at `http://localhost:8000`.

### Frontend Setup

1. **Navigate to the frontend directory:**

    ```bash
    cd ../frontend
    ```

2. **Install dependencies:**

    ```bash
    pnpm install
    ```

3. **Generate the API client:**

    ```bash
    pnpm generate-client
    ```

4. **Run the frontend development server:**

    ```bash
    pnpm dev
    ```

    The frontend will be accessible at `http://localhost:3000` or `http://localhost:3001`.

### Gradio Demo

1. **From the root of the repository, install the required dependencies:**

    ```bash
    pip install gradio
    ```

2. **Run the Gradio demo:**

    ```bash
    python arxflix_gradio.py
    ```

    This will launch a Gradio interface in your browser for easy interaction with the ArXFlix pipeline.

## API Usage Examples

You can interact with the API directly using tools like `curl` or through the frontend.

### Generate Paper Markdown

```bash
curl -X GET "http://localhost:8000/generate_paper/?method=arxiv_html&paper_id=2404.02905"
```

### Generate Script

```bash
curl -X POST "http://localhost:8000/generate_script/?method=openai&paper_id=2404.02905&paper_markdown=<PAPER_MARKDOWN>" -H "Content-Type: application/json"
```

### Generate Assets (Audio, SRT, JSON)

```bash
curl -X POST "http://localhost:8000/generate_assets/?method=elevenlabs&script=<SCRIPT>" -H "Content-Type: application/json"
```

### Generate Video

```bash
curl -X POST "http://localhost:8000/generate_video/?input_dir=<INPUT_DIR>&output_video=output.mp4" -H "Content-Type: application/json"
```

**Note:** Replace placeholders like `<PAPER_MARKDOWN>`, `<SCRIPT>`, and `<INPUT_DIR>` with actual values.

## Configuration

-   **API Keys:** You'll need to set up API keys for services like OpenAI, ElevenLabs, etc. Store these in a `.env` file in the `backend` directory (see `backend/requirements.txt` for required services).
-   **Customization:** You can modify the script generation prompts, audio settings, and video processing parameters within the `backend/utils` files.

## Contributing

Contributions are highly encouraged! Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a pull request against the `main` branch.

Please ensure your code follows the project's coding style and includes appropriate documentation.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=julien-blanchon/arxflix&type=Date)](https://star-history.com/#julien-blanchon/arxflix&Date)

## License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details. Note that some components may have their own licenses (e.g., Remotion).
