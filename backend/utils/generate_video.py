import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from time import sleep
from typing import Literal
import json
import socket

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
    # If a Figure has a local filename (e.g. "figure_1.png"), we prefix it with the URL of the
    # temporary static server so that the browser inside Remotion can retrieve it over HTTP.
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
                    and not item["content"].lower().startswith(("http://", "https://"))
                ):
                    item["content"] = f"http://localhost:{free_port}/{item['content']}"
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
            "localhost",
            "-p",
            free_port,
        ],
        cwd=input.absolute().as_posix(),
    ) as static_server:
        print(f"Exposed directory {input}")
        sleep(2)
        logger.info(f"Exposed directory {input}")
        composition_props = CompositionProps(
            subtitlesFileName=f"http://localhost:{free_port}/subtitles.srt",
            audioFileName=f"http://localhost:{free_port}/audio.wav",
            richContentFileName=f"http://localhost:{free_port}/rich.json",
        )
        logger.info(f"Generating video to {output}")
        subprocess.run(
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
        logger.info(f"Generated video to {output}")
        return output
