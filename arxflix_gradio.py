import gradio as gr
import logging
from backend.main import (
    generate_paper,
    generate_script,
    generate_assets,
    generate_video,
)
from pathlib import Path
import tempfile
import shutil
import dotenv
import os
import time

dotenv.load_dotenv()
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

DEFAULT_METHOD_PAPER = "arxiv_html"
DEFAULT_METHOD_SCRIPT = "openrouter"
DEFAULT_METHOD_AUDIO = "kokoro"
DEFAULT_PAPER_ID = "2404.02905"

VIDEO_DIR = Path("generated_videos")
VIDEO_DIR.mkdir(exist_ok=True)

def _status_working(message: str) -> str:
    """Return HTML for a working status with spinner."""
    return f'<div class="status working"><span class="spinner"></span>{message}</div>'


def _status_done(message: str) -> str:
    """Return HTML for a success status."""
    return f'<div class="status done">✅ {message}</div>'


def _status_error(message: str) -> str:
    """Return HTML for an error status."""
    return f'<div class="status error">❌ {message}</div>'

def process_and_generate_video(
    input_source: str,
    method_paper,
    paper_id,
    method_script,
    method_audio,
    pdf_file,
    api_base_url=None,
):
    """Processes the entire pipeline and generates the video."""
    status = _status_working("Starting the pipeline...")
    yield gr.update(value=status), None  # Update status, no video yet

    temp_dir = None
    try:
        # Validate inputs based on selected source
        if input_source == "Upload PDF":
            if not pdf_file:
                status = "Error: Please upload a PDF file or switch to ArXiv ID."
                yield gr.update(value=status), None
                return
            # When using PDF, we override method/paper_id internally
            use_pdf = True
        else:
            use_pdf = False
            if not paper_id or str(paper_id).strip() == "":
                status = "Error: Please provide a valid ArXiv paper ID or choose Upload PDF."
                yield gr.update(value=status), None
                return

        # Validate local LLM base URL when using local method
        if method_script == "local" and not api_base_url:
            status = "Error: Please provide a Custom LLM API Base URL for the 'local' script method."
            yield gr.update(value=status), None
            return

        # 1. Generate Paper Markdown
        if use_pdf:
            status = _status_working("Generating paper markdown from PDF...")
            yield gr.update(value=status), None
            paper_markdown = generate_paper("pdf", "paper_id", pdf_path=pdf_file)
        else:
            status = _status_working("Generating paper markdown...")
            yield gr.update(value=status), None
            paper_markdown = generate_paper(method_paper, paper_id)
        logger.info("Paper markdown generated successfully.")
        
        # 2. Generate Script
        if use_pdf:
            status = _status_working("Generating script from PDF markdown...")
            yield gr.update(value=status), None
            script = generate_script(
                method_script, paper_markdown, "paper_id", api_base_url, from_pdf=True
            )
        else:
            status = _status_working("Generating script from markdown...")
            yield gr.update(value=status), None
            script = generate_script(
                method_script, paper_markdown, paper_id, api_base_url
            )
        logger.info("Script generated successfully.")

        # 3. Create temporary directory for assets
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        mp3_output = temp_path / "audio.wav"
        srt_output = temp_path / "subtitles.srt"
        rich_output = temp_path / "rich.json"
        input_dir = temp_path
        output_video = temp_path / "output.mp4"

        # 4. Generate Assets
        status = _status_working("Generating audio, subtitles, and rich content assets...")
        yield gr.update(value=status), None
        generate_assets(
            script,
            method_audio,
            mp3_output=str(mp3_output),
            srt_output=str(srt_output),
            rich_output=str(rich_output),
        )
        logger.info("Assets generated successfully.")

        # 5. Generate Video
        status = _status_working("Generating video...")
        yield gr.update(value=status), None
        generate_video(input_dir, output_video)
        logger.info("Video generated successfully.")

        # 6. Move video to the permanent directory
        status = _status_working("Finalizing and saving video...")
        yield gr.update(value=status), None
        final_video_path = VIDEO_DIR / f"video_{paper_id}_{int(time.time())}.mp4"
        shutil.move(str(output_video), str(final_video_path))
        logger.info(f"Video saved to {final_video_path}")

        status = _status_done(f"Pipeline completed! Video saved at: {final_video_path}")
        yield gr.update(value=status), str(final_video_path)  # Return video path as video_output

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        status = _status_error(f"Error: {e}. Check logs for details.")
        yield gr.update(value=status), None  # Return error status, no video

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)


def _toggle_source(choice: str):
    """Toggle visibility and interactivity of inputs based on source choice."""
    if choice == "ArXiv ID":
        return (
            gr.update(visible=True),   # paper_id_input
            gr.update(visible=False),  # pdf_file_input
            gr.update(interactive=True),  # method_paper_input
        )
    else:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(interactive=False),
        )


def _reset_fields():
    """Return default values to reset the UI."""
    return (
        "ArXiv ID",  # input_source
        DEFAULT_METHOD_PAPER,  # method_paper_input
        DEFAULT_PAPER_ID,  # paper_id_input
        DEFAULT_METHOD_SCRIPT,  # method_script_input
        DEFAULT_METHOD_AUDIO,  # method_audio_input
        None,  # pdf_file_input
        None,  # api_base_url
        gr.update(value="Idle..."),  # status_output
        None,  # video_output
    )


# Define Gradio interface
CUSTOM_CSS = """
:root {
  --arx-grad-1: #0ea5e9;
  --arx-grad-2: #8b5cf6;
  --arx-grad-3: #ec4899;
}

body, #root, .gradio-container {
  background:
    radial-gradient(1200px 800px at 10% 10%, rgba(14,165,233,.12), transparent 40%),
    radial-gradient(1000px 600px at 90% 30%, rgba(139,92,246,.12), transparent 50%),
    radial-gradient(800px 600px at 30% 90%, rgba(236,72,153,.12), transparent 50%);
  animation: bgFloat 16s ease-in-out infinite alternate;
}

@keyframes bgFloat {
  0% { background-position: 0 0, 0 0, 0 0; }
  100% { background-position: 30px -30px, -20px 20px, 25px -15px; }
}

#arx-header {
  text-align:center; font-size: 32px; font-weight: 800; margin: 8px 0 4px;
  background: linear-gradient(90deg, var(--arx-grad-1), var(--arx-grad-2), var(--arx-grad-3));
  -webkit-background-clip: text; background-clip:text; color: transparent; letter-spacing: .5px;
}

#arx-sub {text-align:center; color:#a3a3a3; margin: 0 0 18px;}

#controls, #output-panel {
  backdrop-filter: blur(8px);
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,.12);
}

#controls {gap: 12px;}

#actions .gr-button {
  height:48px; font-weight:700; border-radius: 12px;
  transition: transform .15s ease, box-shadow .2s ease, filter .2s ease;
}

#actions .gr-button, #actions .gr-button-primary {
  background: linear-gradient(135deg, var(--arx-grad-1), var(--arx-grad-2));
  color: #fff; border: none;
}

#actions .gr-button:hover {
  transform: translateY(-1px); filter: brightness(1.05);
  box-shadow: 0 10px 20px rgba(139,92,246,.25);
}

#actions .gr-button:active { transform: translateY(0); filter: brightness(.98); box-shadow: none; }

#status-title {margin-bottom:8px;}
#status {min-height:64px; opacity:.98; padding: 12px 14px; border-radius: 12px; background: rgba(17,24,39,.5); border: 1px solid rgba(255,255,255,.06)}

.status { display:flex; align-items:center; gap: 10px; font-weight: 600; }
.status .spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
.status.done { color: #a7f3d0; }
.status.error { color: #fecaca; }

@keyframes spin { to { transform: rotate(360deg); } }

.gr-example { border-radius: 10px; }
"""

with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
    gr.HTML("""
    <div id="arx-header">ArXFlix Video Generator</div>
    <div id="arx-sub">Minimal UI to turn arXiv papers into short videos</div>
    """)

    with gr.Row():
        with gr.Column(scale=1, min_width=360):
            with gr.Group(elem_id="controls"):
                input_source = gr.Radio(
                    ["ArXiv ID", "Upload PDF"],
                    value="ArXiv ID",
                    label="Source",
                    info="Use an arXiv paper ID or upload a PDF to parse",
                )

                paper_id_input = gr.Textbox(
                    label="arXiv Paper ID",
                    value=DEFAULT_PAPER_ID,
                    placeholder="e.g. 2404.02905",
                )

                pdf_file_input = gr.File(
                    label="Upload PDF",
                    file_types=[".pdf"],
                    type="filepath",
                    visible=False,
                )

            with gr.Accordion("Advanced settings", open=False):
                method_paper_input = gr.Dropdown(
                    ["arxiv_gpt", "arxiv_html"],
                    label="Paper Generation Method",
                    value=DEFAULT_METHOD_PAPER,
                    info="How to extract the paper content when using an arXiv ID",
                )

                api_base_url = gr.Textbox(
                    label="Custom LLM API Base URL (optional)",
                    value=None,
                    placeholder="http(s)://host:port/v1 (for local/open-source inference)",
                    visible=False,
                )

            method_script_input = gr.Dropdown(
                ["openai", "local", "gemini", "openrouter", "groq"],
                label="Script Generation Method",
                value=DEFAULT_METHOD_SCRIPT,
            )
            method_audio_input = gr.Dropdown(
                ["elevenlabs", "lmnt", "kokoro"],
                label="Audio Generation Method",
                value=DEFAULT_METHOD_AUDIO,
            )

            with gr.Row(elem_id="actions"):
                generate_button = gr.Button("Generate Video 🚀", variant="primary")
                reset_button = gr.Button("Reset ↺")

            gr.Examples(
                examples=[
                    ["ArXiv ID", DEFAULT_PAPER_ID, "openrouter", "kokoro"],
                    ["ArXiv ID", "2506.05301", "openrouter", "kokoro"],
                ],
                inputs=[input_source, paper_id_input, method_script_input, method_audio_input],
                label="Examples",
            )

        with gr.Column(scale=1):
            with gr.Group(elem_id="output-panel"):
                gr.Markdown("### Progress", elem_id="status-title")
                status_output = gr.Markdown("Idle...", elem_id="status")
                video_output = gr.Video(label="Generated Video")

    # Wire source toggle
    input_source.change(
        _toggle_source,
        inputs=[input_source],
        outputs=[paper_id_input, pdf_file_input, method_paper_input],
    )

    # Generate handler
    generate_button.click(
        process_and_generate_video,
        inputs=[
            input_source,
            method_paper_input,
            paper_id_input,
            method_script_input,
            method_audio_input,
            pdf_file_input,
            api_base_url,
        ],
        outputs=[status_output, video_output],
    )

    def _toggle_api_base(method: str):
        """Show API Base URL only for local method."""
        return gr.update(visible=(method == "local"))

    method_script_input.change(
        _toggle_api_base,
        inputs=[method_script_input],
        outputs=[api_base_url],
    )

    # Reset handler
    reset_button.click(
        _reset_fields,
        inputs=None,
        outputs=[
            input_source,
            method_paper_input,
            paper_id_input,
            method_script_input,
            method_audio_input,
            pdf_file_input,
            api_base_url,
            status_output,
            video_output,
        ],
    )

if __name__ == "__main__":
    demo.queue().launch(share=True)