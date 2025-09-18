"""
Content Classification Module

This module provides functionality to classify markdown content into three categories:
- research: Academic papers, research articles, scientific content
- tutorial: How-to guides, instructional content, step-by-step tutorials
- general: News articles, blog posts, general web content

The classification is performed using OpenRouter with instructor for structured outputs,
following the project's established patterns.
"""

import os
from typing import Dict, Literal, Optional, Any
import logging
from pydantic import BaseModel, Field

# Import required libraries following project pattern
try:
    from openai import OpenAI
    import instructor
    from instructor.hooks import Hooks, HookName
except ImportError:
    OpenAI = None
    instructor = None

# Import our response model
from backend.schemas.content_classification import ContentClassificationResponse, ContentType

logger = logging.getLogger(__name__)

class ContentClassification(BaseModel):
    """Result of content classification - simplified interface for backward compatibility"""
    content_type: str = Field(..., description="The classified content type")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    features: Dict[str, str] = Field(..., description="Extracted features from the content")
    reasoning: str = Field(..., description="Explanation of the classification decision")

class ContentClassifier:
    """
    Classifies markdown content into research, tutorial, or general categories
    using OpenRouter for LLM access, following the project's established pattern.
    """
    
    def __init__(self, 
                 model_name: str = "google/gemini-2.0-flash-001",
                 confidence_threshold: float = 0.7):
        """
        Initialize the content classifier.
        
        Args:
            model_name: OpenRouter model to use for classification
            confidence_threshold: Minimum confidence score for classification
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.client = self._initialize_openrouter_client()
        
        # Classification system prompt
        self.system_prompt = """You are an expert content classifier. Analyze markdown content and classify it into one of three categories:

1. **research**: Academic papers, research articles, scientific studies, technical papers with methodology, results, and citations
2. **tutorial**: How-to guides, instructional content, step-by-step tutorials, educational materials with practical examples  
3. **general**: News articles, blog posts, opinion pieces, general web content, marketing materials

Analyze the content structure, language patterns, purpose, and target audience to make your classification.
Be precise and provide a confidence score between 0.0 and 1.0 based on how certain you are about the classification."""
    
    def _initialize_openrouter_client(self):
        """Initialize OpenRouter client with instructor following the project's pattern"""
        try:
            if OpenAI is None or instructor is None:
                raise ImportError("OpenAI or instructor library not available")
                
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable not set")
                
            openrouter_base_url = "https://openrouter.ai/api/v1"
            
            # Create instructor client following project pattern
            openrouter_client = instructor.from_openai(
                OpenAI(api_key=openrouter_api_key, base_url=openrouter_base_url),
                mode=instructor.Mode.OPENROUTER_STRUCTURED_OUTPUTS if "gpt" not in self.model_name else instructor.Mode.JSON_SCHEMA,
                hooks=self._create_logging_hooks("content_classifier"),
            )
            
            return openrouter_client
                
        except Exception as e:
            logger.warning(f"Failed to initialize OpenRouter client: {str(e)}")
            # Fall back to a simple pattern-based classifier
            return None
    
    def _create_logging_hooks(self, tag: str = "content_classifier") -> Hooks:
        """Create hooks that log each failed attempt, following project pattern"""
        hooks = Hooks()
        state: dict[str, Any] = {"kwargs": None, "response": None}

        def on_kwargs(*args: Any, **kwargs: Any) -> None:
            try:
                state["kwargs"] = {
                    "model": kwargs.get("model"),
                    "messages": kwargs.get("messages")
                    or kwargs.get("contents")
                    or kwargs.get("chat_history"),
                    "temperature": kwargs.get("temperature"),
                    "top_p": kwargs.get("top_p"),
                    "stream": kwargs.get("stream"),
                }
            except Exception:
                pass

        def on_response(response: Any) -> None:
            state["response"] = response

        def extract_text_from_response(resp: Any) -> str | None:
            try:
                if hasattr(resp, "choices") and resp.choices:
                    choice0 = resp.choices[0]
                    if hasattr(choice0, "message") and getattr(choice0.message, "content", None):
                        return str(choice0.message.content)
                    if hasattr(choice0, "text") and getattr(choice0, "text", None):
                        return str(choice0.text)
            except Exception:
                return None
            return None

        def on_parse_error(error: Exception) -> None:
            model = None
            messages = None
            if isinstance(state.get("kwargs"), dict):
                model = state["kwargs"].get("model")
                messages = state["kwargs"].get("messages")
            raw_text = extract_text_from_response(state.get("response"))

            logger.error(f"[{tag}] Parse error: {error}")
            if model:
                logger.error(f"[{tag}] Model: {model}")
            if messages:
                try:
                    user_prompt = None
                    for m in messages:
                        if isinstance(m, dict) and m.get("role") == "user":
                            user_prompt = m.get("content")
                    if user_prompt:
                        excerpt = str(user_prompt)
                        logger.error(f"[{tag}] Prompt excerpt: {excerpt[:1000]}")
                except Exception:
                    pass
            if raw_text:
                logger.error(f"[{tag}] Raw completion excerpt: {raw_text[:1000]}")

        def on_completion_error(error: Exception) -> None:
            logger.error(f"[{tag}] Completion error: {error}")

        def on_last_attempt(error: Exception) -> None:
            logger.error(f"[{tag}] Last attempt failed: {error}")

        hooks.on(HookName.COMPLETION_KWARGS, on_kwargs)
        hooks.on(HookName.COMPLETION_RESPONSE, on_response)
        hooks.on(HookName.PARSE_ERROR, on_parse_error)
        hooks.on(HookName.COMPLETION_ERROR, on_completion_error)
        hooks.on(HookName.COMPLETION_LAST_ATTEMPT, on_last_attempt)
        return hooks

    def _call_openrouter(self, content: str) -> Optional[ContentClassificationResponse]:
        """
        Call OpenRouter to classify content using instructor for structured outputs.
        
        Args:
            content: The markdown content to classify
            
        Returns:
            ContentClassificationResponse or None if failed
        """
        if not self.client:
            return None
            
        # Truncate content if too long (keep first and last parts)
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length//2] + "\n\n[... content truncated ...]\n\n" + content[-max_content_length//2:]
        
        user_prompt = f"""Analyze and classify the following markdown content:

```
{content}
```

Classify this content and provide detailed analysis of the features that led to your classification."""
        
        try:
            response, raw = self.client.chat.completions.create_with_completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ContentClassificationResponse,
                temperature=0.1,
                max_retries=3,
                max_tokens=1000
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter for classification: {str(e)}")
            return None
    
    def _fallback_classification(self, markdown: str) -> ContentClassification:
        """
        Fallback classification using simple heuristics when LLM is not available.
        
        Args:
            markdown: The markdown content to classify
            
        Returns:
            ContentClassification result
        """
        content_lower = markdown.lower()
        
        # Simple heuristic scoring
        research_score = 0
        tutorial_score = 0
        general_score = 0
        
        # Research indicators
        research_keywords = ['abstract', 'methodology', 'results', 'conclusion', 'references', 
                           'hypothesis', 'experiment', 'analysis', 'statistical', 'doi:', 'arxiv:']
        research_score = sum(1 for keyword in research_keywords if keyword in content_lower)
        
        # Tutorial indicators  
        tutorial_keywords = ['step', 'tutorial', 'how to', 'install', 'setup', 'example', 
                           'guide', 'learn', 'create', 'build']
        tutorial_score = sum(1 for keyword in tutorial_keywords if keyword in content_lower)
        
        # Code blocks boost tutorial score
        if '```' in markdown:
            tutorial_score += 3
            
        # General indicators
        general_keywords = ['news', 'announced', 'today', 'recently', 'according to', 
                          'experts', 'industry', 'company', 'market']
        general_score = sum(1 for keyword in general_keywords if keyword in content_lower)
        
        # Determine classification
        scores = {'research': research_score, 'tutorial': tutorial_score, 'general': general_score}
        best_type = max(scores.keys(), key=lambda k: scores[k])
        
        # If all scores are low, default to general
        if max(scores.values()) < 2:
            best_type = "general"
            
        confidence = min(scores[best_type] / 10.0, 1.0)  # Normalize to 0-1
        
        features = {
            "primary_indicators": f"Fallback classification based on keyword matching",
            "content_structure": "Unable to analyze structure without LLM",
            "language_style": "Unable to analyze style without LLM", 
            "target_audience": "Unable to determine audience without LLM"
        }
        
        reasoning = f"Fallback classification as {best_type} based on keyword analysis (OpenRouter unavailable)"
        
        return ContentClassification(
            content_type=best_type,
            confidence_score=confidence,
            features=features,
            reasoning=reasoning
        )

    def classify_content(self, markdown: str) -> ContentClassification:
        """
        Classify markdown content into research, tutorial, or general categories using LLM.
        
        Args:
            markdown: The markdown content to classify
            
        Returns:
            ContentClassification object with type, confidence, features, and reasoning
        """
        if not markdown or not markdown.strip():
            return ContentClassification(
                content_type="general",
                confidence_score=0.0,
                features={
                    "primary_indicators": "Empty content",
                    "content_structure": "No structure",
                    "language_style": "No content",
                    "target_audience": "Unknown"
                },
                reasoning="Empty or invalid content provided"
            )
        
        try:
            # Try OpenRouter classification first
            openrouter_result = self._call_openrouter(markdown)
            
            if openrouter_result:
                logger.info(f"Content classified as {openrouter_result.content_type} with confidence {openrouter_result.confidence_score:.2f}")
                return ContentClassification(
                    content_type=openrouter_result.content_type.value,
                    confidence_score=openrouter_result.confidence_score,
                    features={
                        "primary_indicators": openrouter_result.features.primary_indicators,
                        "content_structure": openrouter_result.features.content_structure,
                        "language_style": openrouter_result.features.language_style,
                        "target_audience": openrouter_result.features.target_audience
                    },
                    reasoning=openrouter_result.reasoning
                )
            else:
                # Fall back to simple heuristics
                logger.warning("OpenRouter classification failed, using fallback method")
                return self._fallback_classification(markdown)
                
        except Exception as e:
            logger.error(f"Error during content classification: {str(e)}")
            # Use fallback classification on error
            return self._fallback_classification(markdown)


# Convenience functions for direct usage
def classify_content(markdown: str, 
                    model_name: str = "google/gemini-2.0-flash-001",
                    confidence_threshold: float = 0.7) -> ContentClassification:
    """
    Classify markdown content using OpenRouter with instructor for structured outputs.
    
    Args:
        markdown: The markdown content to classify
        model_name: OpenRouter model to use for classification
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        ContentClassification result
    """
    classifier = ContentClassifier(
        model_name=model_name,
        confidence_threshold=confidence_threshold
    )
    return classifier.classify_content(markdown)


def extract_content_features(markdown: str) -> Dict[str, str]:
    """
    Extract features from markdown content using OpenRouter analysis with instructor.
    
    Args:
        markdown: The markdown content to analyze
        
    Returns:
        Dictionary of extracted features
    """
    result = classify_content(markdown)
    return result.features


def is_openrouter_available() -> bool:
    """
    Check if OpenRouter is available based on installed libraries and API key.
    
    Returns:
        True if OpenRouter is available, False otherwise
    """
    return (OpenAI is not None and 
            instructor is not None and 
            bool(os.getenv("OPENROUTER_API_KEY")))