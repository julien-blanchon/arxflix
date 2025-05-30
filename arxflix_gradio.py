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
DEFAULT_METHOD_SCRIPT = "openai"
DEFAULT_METHOD_AUDIO = "kokoro"
DEFAULT_PAPER_ID = "2404.02905"

VIDEO_DIR = Path("generated_videos")
VIDEO_DIR.mkdir(exist_ok=True)

def process_and_generate_video(
    method_paper, paper_id, method_script, method_audio, api_base_url=None
):
    """Processes the entire pipeline and generates the video."""
    status = "Starting the pipeline..."
    yield gr.update(value=status), None  # Update status, no video yet

    temp_dir = None
    try:
        # 1. Generate Paper Markdown
        status = "Generating paper markdown..."
        yield gr.update(value=status), None
        paper_markdown = generate_paper(method_paper, paper_id)
        logger.info("Paper markdown generated successfully.")
        
        # 2. Generate Script
        status = "Generating script from markdown..."
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
        status = "Generating audio, subtitles, and rich content assets..."
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
        status = "Generating video..."
        yield gr.update(value=status), None
        generate_video(input_dir, output_video)
        logger.info("Video generated successfully.")

        # 6. Move video to the permanent directory
        status = "Finalizing and saving video..."
        yield gr.update(value=status), None
        final_video_path = VIDEO_DIR / f"video_{paper_id}_{int(time.time())}.mp4"
        shutil.move(str(output_video), str(final_video_path))
        logger.info(f"Video saved to {final_video_path}")

        status = f"Pipeline completed! Video saved at: {final_video_path}"
        yield gr.update(value=status), str(final_video_path)  # Return video path as video_output

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        status = f"Error: {e}. Check logs for details."
        yield gr.update(value=status), None  # Return error status, no video

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)


# Define Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# ArXFlix Video Generator")

    method_paper_input = gr.Dropdown(
        ["arxiv_gpt", "arxiv_html"],
        label="Paper Generation Method",
        value=DEFAULT_METHOD_PAPER,
    )
    paper_id_input = gr.Textbox(label="Arxiv Paper ID", value=DEFAULT_PAPER_ID)
    method_script_input = gr.Dropdown(
        ["openai", "local", "gemini"],
        label="Script Generation Method",
        value=DEFAULT_METHOD_SCRIPT,
    )
    method_audio_input = gr.Dropdown(
        ["elevenlabs", "lmnt", "kokoro"],
        label="Audio Generation Method",
        value=DEFAULT_METHOD_AUDIO,
    )
    api_base_url = gr.Textbox(label="API Base URL (Optional)", value=None)

    generate_button = gr.Button("Generate Video")
    status_output = gr.Textbox(label="Pipeline Status", value="Idle...")
    video_output = gr.Video(label="Generated Video")

    generate_button.click(
        process_and_generate_video,
        inputs=[
            method_paper_input,
            paper_id_input,
            method_script_input,
            method_audio_input,
            api_base_url,
        ],
        outputs=[status_output, video_output],
    )

if __name__ == "__main__":
    demo.launch(share=True)