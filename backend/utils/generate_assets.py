import os
import tempfile
from dotenv import load_dotenv
from elevenlabs import Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs
import pandas as pd
import whisper
import torch
import torchaudio
import srt
from datetime import timedelta
from pathlib import Path
import logging

from backend.types import Text, Caption, Figure, Equation, Headline, RichContent

logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

# Load configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE = Voice(
    voice_id=os.getenv("ELEVENLABS_VOICE_ID", default="lxYfHSkYm1EzQzGhdbfc"),
    settings=VoiceSettings(
        stability=float(os.getenv("ELEVENLABS_STABILITY", default=0.35)),
        similarity_boost=float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", default=0.8)),
        style=0.0,
        use_speaker_boost=True,
    ),
)
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", default="eleven_turbo_v2")


def parse_script(script: str) -> list[RichContent | Text]:
    """Parse the script and return a list of RichContent or Text objects

    Parameters
    ----------
    script : str
        The script to parse as a string

    Returns
    -------
    list[RichContent | Text]
        List of RichContent or Text objects
    """
    lines = script.split("\n")
    content = []
    # For each line, parse it and create the corresponding object
    for line in lines:
        if line.startswith(r"\Figure: "):
            figure_content = line.replace(r"\Figure: ", "")
            figure = Figure(content=figure_content)
            content.append(figure)
        elif line.startswith(r"\Text: "):
            text_content = line.replace(r"\Text: ", "")
            text = Text(content=text_content)
            content.append(text)
        elif line.startswith(r"\Equation: "):
            equation_content = line.replace(r"\Equation: ", "")
            equation = Equation(content=equation_content)
            content.append(equation)
        elif line.startswith(r"\Headline: "):
            headline_content = line.replace(r"\Headline: ", "")
            headline = Headline(content=headline_content)
            content.append(headline)
        else:
            logger.warning(f"Unknown line: {line}")
    return content


def make_caption(result: dict) -> list[Caption]:
    """Create a list of Caption objects from the result of the whisper model

    Parameters
    ----------
    result : dict
        Result dictionary from the whisper model

    Returns
    -------
    list[Caption]
        List of Caption objects
    """
    captions: list[Caption] = []
    for segment in result["segments"]:
        for word in segment["words"]:  # type: ignore
            _word = word["word"]  # type: ignore
            # Remove leading space if there is one
            if _word.startswith(" "):
                _word = _word[1:]
            caption = Caption(word=_word, start=word["start"], end=word["end"])  # type: ignore
            captions.append(caption)
    return captions


def generate_audio_and_caption(
    script_contents: list[RichContent | Text],
    temp_dir: Path = Path(tempfile.gettempdir()),
) -> list[RichContent | Text]:
    """Generate audio and caption for each text segment in the script

    Parameters
    ----------
    script_contents : list[RichContent  |  Text]
        List of RichContent or Text objects
    temp_dir : Path, optional
        Temporary directory to store the audio files, by default Path(tempfile.gettempdir())

    Returns
    -------
    list[RichContent | Text]
        List of RichContent or Text objects with audio and caption
    """
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    # If the temp directory does not exist, create it
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    # For each segment,
    # if it is a rich content, do nothing
    # if it is a text, generate audio and caption and store them in the object
    for i, script_content in enumerate(script_contents):
        match script_content:
            case RichContent(content=content):
                pass
            case Text(content=content, audio=None, captions=None):
                audio_path = (temp_dir / f"audio_{i}.wav").absolute().as_posix()
                # If audio_path don't exist, generate it
                if not os.path.exists(audio_path):
                    logger.info(f"Generating audio {i} at {audio_path}")
                    script_content.audio = elevenlabs_client.generate(
                        text=content,
                        voice=Voice(
                            voice_id="lxYfHSkYm1EzQzGhdbfc",
                            settings=VoiceSettings(
                                stability=0.35,
                                similarity_boost=0.8,
                                style=0.0,
                                use_speaker_boost=True,
                            ),
                        ),
                        model="eleven_turbo_v2",
                    )
                    save(script_content.audio, audio_path)
                audio, sr = torchaudio.load(audio_path)
                model = whisper.load_model("base.en")
                option = whisper.DecodingOptions(
                    language="en",
                    fp16=True,
                    without_timestamps=False,
                    task="transcribe",
                )
                result = model.transcribe(audio_path, word_timestamps=True)
                script_content.captions = make_caption(result)
                script_content.audio_path = audio_path
                total_audio_duration = audio.size(1) / sr
                script_content.end = total_audio_duration

    offset = 0
    # Initially all text caption start at time 0
    # We need to offset them by the end of the previous text
    for i, script_content in enumerate(script_contents):
        if not (isinstance(script_content, Text)):
            continue
        if not script_content.captions:
            continue
        for caption in script_content.captions:
            caption.start += offset
            caption.end += offset
        script_content.start = offset
        if script_content.end:
            script_content.end = script_content.end + offset
        else:
            script_content.end = script_content.captions[-1].end
        offset = script_content.end
    return script_contents


def fill_rich_content_time(
    script_contents: list[RichContent | Text],
) -> list[RichContent | Text]:
    """Fill the time for each rich content based on the text duration

    Parameters
    ----------
    script_contents : list[RichContent  |  Text]
        List of RichContent or Text objects

    Returns
    -------
    list[RichContent | Text]
        List of RichContent or Text objects with time assigned
    """
    # For each rich content, assign a time based on the text duration
    k = 0
    while k < len(script_contents):
        current_rich_content_group = []
        while k < len(script_contents) and not isinstance(script_contents[k], Text):
            current_rich_content_group.append(script_contents[k])
            k += 1

        if k >= len(script_contents):
            break

        next_text_group = []
        while k < len(script_contents) and isinstance(script_contents[k], Text):
            next_text_group.append(script_contents[k])
            k += 1

        if not next_text_group:
            break

        total_duration = next_text_group[-1].end - next_text_group[0].start
        duration_per_rich_content = total_duration / len(current_rich_content_group)
        offset = next_text_group[0].start
        for i, rich_content in enumerate(current_rich_content_group):
            rich_content.start = offset + i * duration_per_rich_content
            rich_content.end = offset + (i + 1) * duration_per_rich_content
            # print(f"Asigning {rich_content.start} - {rich_content.end} to {rich_content}")
    return script_contents


def export_mp3(text_content: list[Text], out_path: str) -> None:
    """Export the audio of the text content to a single mp3 file

    Parameters
    ----------
    text_content : list[Text]
        List of Text objects
    out_path : str
        Path to save the mp3 file
    """
    # Merge all mp3 files into one
    audio_all = []
    for i, text in enumerate(text_content):
        if not text.audio_path:
            continue

        path = text.audio_path
        audio, sr = torchaudio.load(path)
        audio_all.append(audio)
    audio_all_torch = torch.cat(audio_all, dim=1)
    torchaudio.save(out_path, audio_all_torch, sr)


def export_srt(full_audio_path: str, out_path: str) -> None:
    """Export the SRT file for the full audio.
    We use the whisper model again to generate the caption for the full audio
    Because concatenating the caption of each text segment may not be accurate

    Parameters
    ----------
    full_audio_path : str
        Path to the full audio file
    out_path : str
        Path to save the SRT file
    """
    # Generate Caption for the full audio
    model = whisper.load_model("base.en")
    option = whisper.DecodingOptions(
        language="en", fp16=True, without_timestamps=False, task="transcribe"
    )
    result = model.transcribe(full_audio_path, word_timestamps=True)
    flatten_caption = make_caption(result)
    # Generate SRT file from the caption
    subs = [
        srt.Subtitle(
            index=i,
            start=timedelta(seconds=t.start),
            end=timedelta(seconds=t.end),
            content=t.word,
        )
        for i, t in enumerate(flatten_caption)
    ]
    srt_text = srt.compose(subs)
    # Write the SRT file
    with open(out_path, "w") as f:
        f.write(srt_text)


def export_rich_content_json(rich_content: list[RichContent], out_path: str) -> None:
    """Export the rich content to a json file

    Parameters
    ----------
    rich_content : list[RichContent]
        List of RichContent objects
    out_path : str
        Path to save the json file
    """
    # Export rich content to json
    rich_content_dict = []
    for i, content in enumerate(rich_content):
        content_dict = {
            "type": content.__class__.__name__.lower(),
            "content": content.content,
            "start": content.start,
            "end": content.end,
        }
        rich_content_dict.append(content_dict)
    df = pd.DataFrame(rich_content_dict)
    df.to_json(out_path, orient="records")
