from pathlib import Path
import logging
import os
import tempfile
from typing import Literal
from dotenv import load_dotenv
import typer
import fastapi
from fastapi.middleware.cors import CORSMiddleware

from backend.utils import (
    process_video,
)
from backend.utils import (
    generate_audio_and_caption,
    fill_rich_content_time,
    export_mp3,
    export_srt,
    export_rich_content_json,
)
from backend.utils import process_article
from backend.utils import process_script
from backend.type import Text, RichContent

# Load logger
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

# Create CLI and API
cli = typer.Typer()
api = fastapi.FastAPI()

# Add CORS middleware to API
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@cli.command("generate_paper")
@api.get("/generate_paper/")
def generate_paper(method: Literal["arxiv_gpt", "arxiv_html"], paper_id: str) -> str:
    """Generate paper markdown using ArxivGPT or ArxivHTML api

    Parameters
    ----------
    method : "arxiv_gpt" | "arxiv_html"
        The method to generate paper markdown
    paper_id : str
        The paper id to generate markdown

    Returns
    -------
    str
        The paper markdown
    """
    logger.info(
        f"Generating paper markdown using method: {method} and paper_id: {paper_id}"
    )
    paper = process_article(method, paper_id)
    return paper


@cli.command("generate_script")
@api.post("/generate_script/")
def generate_script(method: Literal["openai","local","gemini"], paper_markdown: str,paper_id: str, end_point_base_url : str=None) -> str:
    """Generate video script from paper markdown using an LLM

    Parameters
    ----------
    method : "openai"
        The method to generate script
    paper_markdown : str
        The paper markdown

    Returns
    -------
    str
        The video script
    """
    logger.info(f"Generating script from paper: \n{paper_markdown}")
    script = process_script(method, paper_markdown,paper_id,end_point_base_url)
    return script


@cli.command("generate_assets")
@api.post("/generate_assets/")
def generate_assets(
    script: str,
    method: Literal["elevenlabs", "lmnt"],
    mp3_output: str = "public/audio.wav",
    srt_output: str = "public/output.srt",
    rich_output: str = "public/output.json",
) -> float:
    """Generate audio, caption, and rich content assets from script

    Parameters
    ----------
    script : str
        The video script
    method : "elevenlabs" | "lmnt"
        The method to generate audio
    mp3_output : str, optional
        The output mp3 file path, by default "public/audio.wav"
    srt_output : str, optional
        The output srt file path, by default "public/output.srt"
    rich_output : str, optional
        The output rich content json file path, by default "public/output.json

    Returns
    -------
    float
        The total duration of the audio
    """
    logger.info(f"Generating assets from script: {script}")

    # Create a temporary directory
    temp_dir = tempfile.TemporaryDirectory()
    logger.info(f"Created temporary directory: {temp_dir}")

    # Create parent directory for mp3_output, srt_output, and rich_output
    os.makedirs(os.path.dirname(mp3_output), exist_ok=True)
    os.makedirs(os.path.dirname(srt_output), exist_ok=True)
    os.makedirs(os.path.dirname(rich_output), exist_ok=True)

    # Generate audio and caption for each text content
    script_contents = generate_audio_and_caption(method, script)
    # Fill the time for each RichContent
    script_contents = fill_rich_content_time(script_contents)

    # Separate rich content and text content
    rich_content = [c for c in script_contents if isinstance(c, RichContent)]
    text_content = [c for c in script_contents if isinstance(c, Text)]

    # Export mp3
    export_mp3(text_content, mp3_output, offset=0.5)

    # Export srt
    export_srt(mp3_output, srt_output)

    # Export rich content
    export_rich_content_json(rich_content, rich_output)

    # Remove temp_dir
    temp_dir.cleanup()

    total_duration = text_content[-1].end if text_content[-1].end else 0
    return total_duration


@cli.command("generate_video")
@api.post("/generate_video/")
def generate_video(
    input_dir: str,
    output_video: str,
):
    """Generate video from input directory.
    The input directory should contain subtitles.srt, audio.wav, and rich.json files.

    Parameters
    ----------
    input_dir : str
        The input directory containing subtitles.srt, audio.wav, and rich.json
    output_video : str
        Path of the output video
    """
    _input_dir = Path(input_dir)
    _output_video = Path(output_video)

    logger.info(f"Generating video to {_output_video.name} from {_input_dir.name}")

    if not _input_dir.exists() or not _input_dir.is_dir():
        raise FileNotFoundError(f"Input directory {_input_dir} does not exist")

    if not (_input_dir / "subtitles.srt").exists():
        raise FileNotFoundError(f"Subtitles file does not exist in {_input_dir}")
    if not (_input_dir / "audio.wav").exists():
        raise FileNotFoundError(f"Audio file does not exist in {_input_dir}")
    if not (_input_dir / "rich.json").exists():
        raise FileNotFoundError(f"Rich content file does not exist in {_input_dir}")

    process_video(_input_dir, _output_video)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    logging.info("info")
    cli()
