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
REMOTION_CONCURRENCY = 1

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
    introFileName: str = "frontend/public/intro.txt"
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
        sleep(60)
        logger.info(f"Exposed directory {input}")
        composition_props = CompositionProps(
            introFileName=f"http://localhost:{free_port}/intro.txt",
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
