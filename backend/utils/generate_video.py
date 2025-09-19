import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from time import sleep
from typing import Literal
import json
import socket
import requests
import hashlib
from urllib.parse import urlparse
import os

VIDEO_FPS = 30
VIDEO_HEIGHT = 1080
VIDEO_WIDTH = 1920
REMOTION_ROOT_PATH = Path("frontend/src/remotion/index.ts")
REMOTION_COMPOSITION_ID = "Arxflix"
REMOTION_CONCURRENCY = 6

logger = logging.getLogger(__name__)


def get_free_port():
    sock = socket.socket()
    sock.bind(("", 0))
    free_port = str(sock.getsockname()[1])
    sock.close()
    return free_port


@dataclass
class CompositionProps:
    durationInSeconds: int = 5
    subtitlesFileName: str = "frontend/public/output.srt"
    audioFileName: str = "frontend/public/audio.wav"
    richContentFileName: str = "frontend/public/output.json"
    waveColor: str = "#a3a5ae"
    subtitlesLinePerPage: int = 2
    subtitlesLineHeight: int = 98
    subtitlesZoomMeasurerSize: int = 10
    onlyDisplayCurrentSentence: bool = True
    mirrorWave: bool = False
    waveLinesToDisplay: int = 300
    waveFreqRangeStartIndex: int = 5
    waveNumberOfSamples: Literal["32", "64", "128", "256", "512"] = "512"
    durationInFrames: int = field(init=False)

    def __post_init__(self):
        self.durationInFrames: int = self.durationInSeconds * VIDEO_FPS + 7 * VIDEO_FPS


def download_external_image(url: str, cache_dir: Path) -> str:
    """Download an external image and return the local filename.
    
    Args:
        url: The external image URL
        cache_dir: Directory to cache downloaded images
        
    Returns:
        Local filename of the downloaded image
    """
    try:
        # Create a hash-based filename to avoid conflicts
        url_hash = hashlib.md5(url.encode()).hexdigest()
        parsed_url = urlparse(url)
        file_extension = os.path.splitext(parsed_url.path)[1] or '.png'
        local_filename = f"cached_{url_hash}{file_extension}"
        local_path = cache_dir / local_filename
        
        # Download if not already cached
        if not local_path.exists():
            logger.info(f"Downloading external image: {url}")
            
            # Use headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Write the image data
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded and cached: {local_filename}")
        else:
            logger.info(f"Using cached image: {local_filename}")
            
        return local_filename
        
    except Exception as e:
        logger.error(f"Failed to download image {url}: {e}")
        # Return a placeholder or the original URL as fallback
        return "placeholder.png"


def expose_directory(directory: Path):
    # pnpx http-server --cors -a localhost -p 8080
    subprocess.run(
        [
            "pnpx",
            "http-server",
            "--cors",
            "-a",
            "localhost",
            "-p",
            "8080",
        ],
        cwd=directory.absolute().as_posix(),
    )


def process_video(
    input: Path,
    output: Path = Path("frontend/public/output.mp4"),
):
    # Get the paper id,
    # Pick an available port,
    free_port = get_free_port()
    print(f"Free port: {free_port}")
    # Ensure that figures inside the Rich Content JSON can be fetched by the Remotion bundle.
    # Download external images and update references to local files.
    rich_json_path = input / "rich.json"
    if rich_json_path.exists():
        try:
            data = json.loads(rich_json_path.read_text())
            # The JSON is expected to be a list of dicts.
            for item in data:
                if (
                    isinstance(item, dict)
                    and item.get("type") == "figure"
                    and isinstance(item.get("content"), str)
                ):
                    content_url = item["content"]
                    
                    if content_url.lower().startswith(("http://", "https://")):
                        # Download external image and replace with local reference
                        try:
                            local_filename = download_external_image(content_url, input)
                            item["content"] = f"http://127.0.0.1:{free_port}/{local_filename}"
                            logger.info(f"Replaced external URL {content_url} with local {local_filename}")
                        except Exception as e:
                            logger.error(f"Failed to download {content_url}: {e}")
                            # Keep original URL as fallback (may still fail)
                            pass
                    else:
                        # Local file - prefix with server URL
                        item["content"] = f"http://127.0.0.1:{free_port}/{content_url}"
                        
            rich_json_path.write_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to rewrite {rich_json_path} with absolute URLs: {e}")
    with subprocess.Popen(
        [
            "pnpx",
            "http-server",
            input.absolute().as_posix(),
            "--cors",
            "-a",
            "0.0.0.0",
            "-p",
            free_port,
        ],
        cwd=input.absolute().as_posix(),
    ) as static_server:
        print(f"Exposed directory {input}")
        sleep(2)
        logger.info(f"Exposed directory {input}")
        # Use IPv4 to avoid environments where localhost resolves to IPv6 ::1
        base_url = f"http://127.0.0.1:{free_port}"
        composition_props = CompositionProps(
            subtitlesFileName=f"{base_url}/subtitles.srt",
            audioFileName=f"{base_url}/audio.wav",
            richContentFileName=f"{base_url}/rich.json",
        )
        logger.info(f"Generating video to {output}")
        render_proc = subprocess.run(
            [
                "npx",
                "remotion",
                "render",
                REMOTION_ROOT_PATH.absolute().as_posix(),
                "--props",
                json.dumps(asdict(composition_props)),
                "--compositionId",
                REMOTION_COMPOSITION_ID,
                "--concurrency",
                str(REMOTION_CONCURRENCY),
                "--output",
                output.absolute().as_posix(),
            ],
            cwd=Path("frontend").absolute().as_posix(),
        )
        static_server.terminate()
        if render_proc.returncode != 0:
            raise RuntimeError(f"Remotion render failed with exit code {render_proc.returncode}")
        if not output.exists():
            raise FileNotFoundError(str(output))
        logger.info(f"Generated video to {output}")
        return output
