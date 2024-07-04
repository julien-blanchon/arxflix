import asyncio
from pathlib import Path
import logging
import os
import tempfile
from dotenv import load_dotenv
from pydantic import BaseModel
import typer
import fastapi

from backend.utils.generate_video import (
    process_video,
)
from backend.utils.generate_assets import (
    generate_audio_and_caption_lmnt,
    fill_rich_content_time,
    export_mp3,
    export_srt,
    export_rich_content_json,
    parse_script,
)
from backend.utils.generate_paper import process_article
from backend.utils.generate_script import process_script
from backend.utils.huggingface import publish_post
from backend.types import Text, RichContent

# Load logger
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

# Create CLI and API
cli = typer.Typer()
api = fastapi.FastAPI()


@cli.command("generate_paper")
@api.get("/generate_paper/")
def generate_paper(url: str, store: str = "") -> str:
    logger.info(f"Generating paper from URL: {url}")
    # Also possible with https://r.jina.ai/{url}
    paper = process_article(url)
    if store and store != "":
        with open(store, "w") as f:
            f.write(paper)
    return paper


@cli.command("generate_script")
def generate_script(
    paper: str, url: str, use_path: bool = True, store: str = ""
) -> tuple[str, str]:
    logger.info(f"Generating script from paper: {paper}")
    if use_path:
        paper_path = paper
        paper = open(paper_path, "r").read()
    script, intro = process_script(paper, url)
    if store and store != "":
        with open(store, "w") as f:
            f.write(script)
        with open(store.replace("script.txt", "intro.txt"), "w") as f:
            f.write(intro)
    return script, intro


class InputGenerateScript(BaseModel):
    paper: str
    use_path: bool = False


@api.post("/generate_script/")
def generate_script_api(input: InputGenerateScript) -> tuple[str, str]:
    paper = input.paper
    use_path = input.use_path
    script, intro = generate_script(paper, "", use_path)
    return script, intro


@cli.command("generate_assets")
def generate_assets(
    script: str,
    use_path: bool = True,
    mp3_output: str = "public/audio.wav",
    srt_output: str = "public/output.srt",
    rich_output: str = "public/output.json",
) -> float:
    logger.info(f"Generating assets from script: {script}")
    # Create a temporary directory
    # temp_dir = Path(tempfile.TemporaryDirectory().name)
    temp_dir = tempfile.TemporaryDirectory()
    logger.info(f"Created temporary directory: {temp_dir}")

    # Create parent directory for mp3_output, srt_output, and rich_output
    os.makedirs(os.path.dirname(mp3_output), exist_ok=True)
    os.makedirs(os.path.dirname(srt_output), exist_ok=True)
    os.makedirs(os.path.dirname(rich_output), exist_ok=True)

    # Parse the script to list[RichContent | Text]
    if use_path:
        script_path = script
        script = open(script_path, "r").read()
    script_contents = parse_script(script)
    # Generate audio and caption for each text content
    # script_contents = generate_audio_and_caption(script_contents, temp_dir=temp_dir)
    script_contents = asyncio.run(
        generate_audio_and_caption_lmnt(script_contents, temp_dir=Path(temp_dir.name))
    )
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


class InputGenerateAssets(BaseModel):
    script: str
    use_path: bool = False
    mp3_output: str = "public/audio.wav"
    srt_output: str = "public/output.srt"
    rich_output: str = "public/output.json"


@api.post("/generate_assets/")
def generate_assets_api(
    input: InputGenerateAssets,
) -> float:
    script = input.script
    use_path = input.use_path
    mp3_output = input.mp3_output
    srt_output = input.srt_output
    rich_output = input.rich_output
    total_duration = generate_assets(
        script, use_path, mp3_output, srt_output, rich_output
    )
    return total_duration


@cli.command("generate_video")
@api.post("/generate_video/")
def generate_video(
    input_dir: Path,
    output_video: Path,
):
    logger.info(f"Generating video to {output_video.name}")
    process_video(input_dir, output_video)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    logging.info("info")
    cli()


@cli.command("publish_post")
@api.post("/publish_post/")
def publish_post_command(
    paper_id: str,
    title: str,
    video_path: Path,
):
    logger.info(f"Publishing post with id: {id}")
    publish_post(paper_id=paper_id, title=title, video_path=video_path)
