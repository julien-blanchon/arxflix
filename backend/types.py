from dataclasses import dataclass
from typing import Iterator


@dataclass
class Caption:
    word: str
    start: float
    end: float


@dataclass
class RichContent:
    content: str
    start: float | None = None
    end: float | None = None


@dataclass
class Figure(RichContent):
    pass


@dataclass
class Text:
    content: str
    audio: bytes | Iterator[bytes] | None = None
    audio_path: str | None = None
    captions: list[Caption] | None = None
    start: float | None = None
    end: float | None = None
    pass


@dataclass
class Equation(RichContent):
    pass


@dataclass
class Headline(RichContent):
    pass
