import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Literal
import json

VIDEO_FPS = 30
VIDEO_HEIGHT = 1080
VIDEO_WIDTH = 1920
REMOTION_ROOT_PATH = Path("frontend/remotion/index.ts")
REMOTION_COMPOSITION_ID = "Arxflix"
REMOTION_CONCURRENCY = 1


@dataclass
class CompositionProps:
    durationInSeconds: int = 5
    audioOffsetInSeconds: int = 0
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
        self.durationInFrames: int = self.durationInSeconds * VIDEO_FPS


def process_video(
    composition_props: CompositionProps = CompositionProps(),
    output: Path = Path("frontend/public/output.mp4"),
):
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
        ]
    )
