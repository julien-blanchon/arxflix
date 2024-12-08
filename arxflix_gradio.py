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
# Configure logging
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

# Define default values for inputs
DEFAULT_METHOD_PAPER = "arxiv_html"
DEFAULT_METHOD_SCRIPT = "openai"
DEFAULT_METHOD_AUDIO = "elevenlabs"
DEFAULT_PAPER_ID = "2404.02905"  # Example paper ID


VIDEO_DIR = Path("generated_videos")  # Directory to store videos permanently
VIDEO_DIR.mkdir(exist_ok=True)

def process_and_generate_video(
    method_paper, paper_id, method_script, method_audio, api_base_url=None
):
    """Processes the entire pipeline and generates the video."""

    try:
        # 1. Generate Paper Markdown
        paper_markdown = generate_paper(method_paper, paper_id)
        logger.info("Generated paper markdown successfully.")

        # 2. Generate Script
        script = generate_script(
            method_script, paper_markdown, paper_id, api_base_url
        )
        logger.info("Generated script successfully.")

        # 3. Create temporary directory for assets
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        mp3_output = temp_path / "audio.wav"
        srt_output = temp_path / "subtitles.srt"
        rich_output = temp_path / "rich.json"
        input_dir = temp_path
        output_video = temp_path / "output.mp4"

        # 4. Generate Assets
        generate_assets(
            script,
            method_audio,
            mp3_output=str(mp3_output),
            srt_output=str(srt_output),
            rich_output=str(rich_output),
        )
        logger.info("Generated assets successfully.")


        # Copy necessary files to the temporary directory
        (input_dir / "audio.wav").rename(input_dir / "audio.wav")  # Ensure correct format
        (input_dir / "subtitles.srt").rename(input_dir / "subtitles.srt")
        (input_dir / "rich.json").rename(input_dir / "rich.json")

        # 5. Generate Video
        generate_video(input_dir, output_video)
        logger.info("Generated video successfully.")

        # 6. Move video to permanent location
        final_video_path = VIDEO_DIR / f"video_{paper_id}_{int(time.time())}.mp4"  # Unique filename
        shutil.move(str(output_video), str(final_video_path))
        logger.info(f"Video saved to {final_video_path}")

        return gr.update(value=final_video_path)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return gr.update(value="Error generating video. Check logs for details.")
    finally:
        # Clean up the temporary directory after video generation and display (or error).
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
        ["elevenlabs", "lmnt"], label="Audio Generation Method", value=DEFAULT_METHOD_AUDIO
    )
    api_base_url = gr.Textbox(label="API Base URL (Optional)", value=None)


    generate_button = gr.Button("Generate Video")
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
        outputs=video_output,
    )

if __name__ == "__main__":
    demo.launch(share=True)