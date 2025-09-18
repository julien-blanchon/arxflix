"""
Pydantic models for content classification responses.

This module defines the structured response format for content classification
using instructor with OpenRouter, following the project's established patterns.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Dict
from enum import Enum

class ContentType(str, Enum):
    """Enumeration of supported content types"""
    RESEARCH = "research"
    TUTORIAL = "tutorial" 
    GENERAL = "general"

class ContentFeatures(BaseModel):
    """Features extracted from content during classification"""
    primary_indicators: str = Field(
        ...,
        description="Main features that led to this classification",
        examples=[
            "Abstract, methodology, results, citations",
            "Step-by-step instructions, code examples, how-to language",
            "News-style writing, temporal references, general topics"
        ]
    )
    content_structure: str = Field(
        ...,
        description="Overall structure and organization of the content",
        examples=[
            "Academic paper structure with clear sections",
            "Sequential instructional format",
            "Article format with news-style organization"
        ]
    )
    language_style: str = Field(
        ...,
        description="Writing style and tone of the content",
        examples=[
            "Formal academic writing",
            "Instructional and practical",
            "Journalistic and accessible"
        ]
    )
    target_audience: str = Field(
        ...,
        description="Intended audience for the content",
        examples=[
            "Researchers and academics",
            "Learners and practitioners", 
            "General public"
        ]
    )

class ContentClassificationResponse(BaseModel):
    """Structured response for content classification"""
    content_type: ContentType = Field(
        ...,
        description="Classified content type: research, tutorial, or general"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 for the classification"
    )
    features: ContentFeatures = Field(
        ...,
        description="Detailed features extracted from the content"
    )
    reasoning: str = Field(
        ...,
        description="Detailed explanation of why the content was classified this way",
        min_length=20,
        examples=[
            "Content contains clear academic structure with abstract, methodology, results, and citations typical of research papers",
            "Content follows tutorial format with step-by-step instructions and practical examples",
            "Content appears to be general news or blog content with journalistic style"
        ]
    )

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v):
        """Ensure confidence score is within valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

    @field_validator('reasoning')
    @classmethod
    def validate_reasoning(cls, v):
        """Ensure reasoning is meaningful and not empty"""
        if len(v.strip()) < 20:
            raise ValueError('Reasoning must be at least 20 characters long')
        return v.strip()