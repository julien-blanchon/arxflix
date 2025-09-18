"""
Overview generators for different content types.

This module provides specialized overview generation for research papers, tutorials,
and general content, each with content-type-specific prompts and formatting.
"""

from typing import Literal, Optional, Dict, Any
from openai import OpenAI
from backend.schemas.script import (
    generate_model_with_context_check, 
    generate_tutorial_model_with_context_check,
    generate_general_model_with_context_check,
    reconstruct_script
)
import instructor
from instructor.hooks import Hooks, HookName
import os
import google.generativeai as genai
import logging
import traceback
from groq import Groq

logger = logging.getLogger(__name__)


def create_logging_hooks(tag: str = "instructor") -> Hooks:
    """Create hooks that log each failed attempt (completion + parse errors)."""
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


# Research overview prompt - uses existing research-focused approach
RESEARCH_OVERVIEW_PROMPT = r"""
<context>
You're Arxflix an AI Researcher and Content Creator on Youtube who specializes in summarizing academic papers.
The video will be uploaded on YouTube and is intended for a research-focused audience of academics, students, and professionals of the field of deep learning. 
</context>

<goal>
Generate a script for a mid-short video (5-6 minutes or less than 6000 words) on the research paper you will receive.
</goal>

<style_instructions>
The script should be engaging, clear, and concise, effectively communicating the content of the paper. 
The video should give a good overview of the paper in the least amount of time possible, with short sentences that fit well for a dynamic Youtube video.
The overall goal of the video is to make research papers more accessible and understandable to a wider audience, while maintaining academic rigor.
Focus on methodology, findings, implications, and technical details that matter to researchers.
</style_instructions>

<format_instructions>
The script should be formatted following the following rules below:
- Your output is a JSON with the following keys:
    - title: The title of the video.
    - paper_id: The id of the paper or "general_content" for non-arXiv content
    - target_duration_minutes: The target duration of the video
    - components: a list of component (component_type, content, position)
        - You should follow this format for each component: Text, Figure, Equation and Headline
        - The only authorized component_type are: Text, Figure, Equation and Headline
        - Figure, Equation (latex) and Headline will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
        - The Text will be spoken by a narrator and caption in the video.
        - Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
        - For Equation: Don't use $ or [, the latex context is automatically detected.
        - For Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
        - Don't hallucinate figures.
        - For research content, emphasize methodology, results, and implications.
</format_instructions>

Your output is a JSON with the following structure:

{
    "title": "...",
    "paper_id": "...",
    "target_duration_minutes": ...,
    "components": [
        {
            "component_type": "...",
            "content": "...",
            "position": ...
        },
        ...
    ]
}
"""

# Tutorial overview prompt - focused on learning and instruction
TUTORIAL_OVERVIEW_PROMPT = r"""
<context>
You're Arxflix an AI Content Creator on Youtube who specializes in creating educational content from tutorial and instructional materials.
The video will be uploaded on YouTube and is intended for learners, students, and professionals who want to understand and apply the concepts being taught.
</context>

<goal>
Generate a script for a mid-short video (5-6 minutes or less than 6000 words) on the tutorial content you will receive.
</goal>

<style_instructions>
The script should be engaging, clear, and educational, effectively communicating the learning objectives and key concepts.
The video should provide a comprehensive overview of the tutorial in the least amount of time possible, with short sentences that fit well for a dynamic Youtube video.
Focus on learning objectives, step-by-step breakdowns, practical applications, and key concepts that learners need to understand.
Emphasize how-to aspects, examples, and practical implementation details.
Make complex concepts accessible to learners at different levels.
</style_instructions>

<format_instructions>
The script should be formatted following the following rules below:
- Your output is a JSON with the following keys:
    - title: The title of the video.
    - target_duration_minutes: The target duration of the video
    - components: a list of component (component_type, content, position)
        - You should follow this format for each component: Text, Figure, Equation, Headline, and Code_Snippet
        - The only authorized component_type are: Text, Figure, Equation, Headline, and Code_Snippet
        - IMPORTANT: The script MUST start with a Headline component at position 0
        - Figure, Equation (latex), Headline, and Code_Snippet will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
        - The Text will be spoken by a narrator and caption in the video.
        - Code_Snippet should contain actual code examples from the tutorial content, formatted as plain text without markdown code blocks.
        - Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
        - For Equation: Don't use $ or [, the latex context is automatically detected.
        - For Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
        - For Code_Snippet: Include relevant code examples that help illustrate the concepts being taught.
        - Don't hallucinate figures or code snippets.
        - For tutorial content, emphasize learning objectives, step-by-step processes, and practical applications.
        - Highlight code examples and implementation details when present.
</format_instructions>

Your output is a JSON with the following structure:

{
    "title": "...",
    "target_duration_minutes": ...,
    "components": [
        {
            "component_type": "...",
            "content": "...",
            "position": ...
        },
        ...
    ]
}
"""

# General overview prompt - focused on key points and takeaways
GENERAL_OVERVIEW_PROMPT = r"""
<context>
You're Arxflix an AI Content Creator on Youtube who specializes in creating engaging summaries of various web content.
The video will be uploaded on YouTube and is intended for a general audience who wants to quickly understand the main points and key takeaways from the content.
</context>

<goal>
Generate a script for a mid-short video (5-6 minutes or less than 6000 words) on the general content you will receive.
</goal>

<style_instructions>
The script should be engaging, clear, and accessible, effectively communicating the main points and key takeaways.
The video should provide a comprehensive overview of the content in the least amount of time possible, with short sentences that fit well for a dynamic Youtube video.
Focus on main points, key takeaways, essential information, and context that helps viewers understand the significance.
Make the content accessible to a broad audience while maintaining the core message.
Emphasize practical relevance and real-world implications.
</style_instructions>

<format_instructions>
The script should be formatted following the following rules below:
- Your output is a JSON with the following keys:
    - title: The title of the video.
    - target_duration_minutes: The target duration of the video
    - components: a list of component (component_type, content, position)
        - You should follow this format for each component: Text, Figure, Equation, Headline, and Code_Snippet
        - The only authorized component_type are: Text, Figure, Equation, Headline, and Code_Snippet
        - IMPORTANT: The script MUST start with a Headline component at position 0
        - Figure, Equation (latex), Headline, and Code_Snippet will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
        - The Text will be spoken by a narrator and caption in the video.
        - Code_Snippet should contain relevant code examples when present in the content, formatted as plain text without markdown code blocks.
        - Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
        - For Equation: Don't use $ or [, the latex context is automatically detected.
        - For Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
        - For Code_Snippet: Include relevant code examples when they help illustrate key concepts or practical applications.
        - Don't hallucinate figures or code snippets.
        - For general content, emphasize main points, key takeaways, and practical relevance.
        - Focus on making complex topics accessible to a general audience.
</format_instructions>

Your output is a JSON with the following structure:

{
    "title": "...",
    "target_duration_minutes": ...,
    "components": [
        {
            "component_type": "...",
            "content": "...",
            "position": ...
        },
        ...
    ]
}
"""


def _generate_overview_openai(
    content: str, 
    content_type: Literal["research", "tutorial", "general"],
    source_identifier: str
) -> str:
    """Generate overview using OpenAI GPT models."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

    if not OPENAI_API_KEY:
        raise ValueError("You need to set the OPENAI_API_KEY environment variable.")

    # Select appropriate prompt based on content type
    if content_type == "research":
        system_prompt = RESEARCH_OVERVIEW_PROMPT
    elif content_type == "tutorial":
        system_prompt = TUTORIAL_OVERVIEW_PROMPT
    else:  # general
        system_prompt = GENERAL_OVERVIEW_PROMPT

    openai_client = instructor.from_openai(
        OpenAI(api_key=OPENAI_API_KEY),
        mode=instructor.Mode.JSON_SCHEMA,
        hooks=create_logging_hooks("openai"),
    )
    
    # Select appropriate response model based on content type
    if content_type == "research":
        response_model = generate_model_with_context_check(source_identifier, content)
    elif content_type == "tutorial":
        response_model = generate_tutorial_model_with_context_check(source_identifier, content)
    else:  # general
        response_model = generate_general_model_with_context_check(source_identifier, content)

    response, raw = openai_client.chat.completions.create_with_completion(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the {content_type} content I want you to generate a script from, source identifier is {source_identifier}: " + content},
        ],
        response_model=response_model,
        temperature=0,
        max_retries=3
    )

    try:
        result = reconstruct_script(response)
    except Exception as e:
        logger.error(f"Script reconstruction failed: {e}")
        raise ValueError(f"The model failed the script generation: {e}")
    
    return result


def _generate_overview_openrouter(
    content: str, 
    content_type: Literal["research", "tutorial", "general"],
    source_identifier: str
) -> str:
    """Generate overview using OpenRouter."""
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("SCRIPGENETOR_MODEL", "google/gemini-2.0-flash-001")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    if not OPENROUTER_API_KEY:
        raise ValueError("You need to set the OPENROUTER_API_KEY environment variable.")

    # Select appropriate prompt based on content type
    if content_type == "research":
        system_prompt = RESEARCH_OVERVIEW_PROMPT
    elif content_type == "tutorial":
        system_prompt = TUTORIAL_OVERVIEW_PROMPT
    else:  # general
        system_prompt = GENERAL_OVERVIEW_PROMPT

    openrouter_client = instructor.from_openai(
        OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL),
        mode=instructor.Mode.OPENROUTER_STRUCTURED_OUTPUTS if "gpt" not in OPENROUTER_MODEL else instructor.Mode.JSON,
        hooks=create_logging_hooks("openrouter"),
    )
    
    # Select appropriate response model based on content type
    if content_type == "research":
        response_model = generate_model_with_context_check(source_identifier, content)
    elif content_type == "tutorial":
        response_model = generate_tutorial_model_with_context_check(source_identifier, content)
    else:  # general
        response_model = generate_general_model_with_context_check(source_identifier, content)

    response, raw = openrouter_client.chat.completions.create_with_completion(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the {content_type} content I want you to generate a script from, source identifier is {source_identifier}: " + content},
        ],
        response_model=response_model,
        temperature=0,
        max_retries=3,
        max_tokens=8000,
    )

    try:
        result = reconstruct_script(response)
    except Exception as e:
        logger.error(f"Script reconstruction failed: {e}")
        raise ValueError(f"The model failed the script generation: {e}, {traceback.format_exc()}")
    
    return result


def _generate_overview_gemini(
    content: str, 
    content_type: Literal["research", "tutorial", "general"],
    source_identifier: str
) -> str:
    """Generate overview using Google Gemini."""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

    if not GEMINI_API_KEY:
        raise ValueError("You need to set the GEMINI_API_KEY environment variable.")

    genai.configure(api_key=GEMINI_API_KEY)

    # Define safety settings
    safe = [
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # Select appropriate prompt based on content type
    if content_type == "research":
        system_prompt = RESEARCH_OVERVIEW_PROMPT
    elif content_type == "tutorial":
        system_prompt = TUTORIAL_OVERVIEW_PROMPT
    else:  # general
        system_prompt = GENERAL_OVERVIEW_PROMPT

    gemini_client = instructor.from_gemini(
        client=genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            safety_settings=safe,
            generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
        ),
        mode=instructor.Mode.GEMINI_JSON,
        hooks=create_logging_hooks("gemini"),
    )

    try:
        # Select appropriate response model based on content type
        if content_type == "research":
            response_model = generate_model_with_context_check(source_identifier, content)
        elif content_type == "tutorial":
            response_model = generate_tutorial_model_with_context_check(source_identifier, content)
        else:  # general
            response_model = generate_general_model_with_context_check(source_identifier, content)

        response, raw = gemini_client.chat.completions.create_with_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the {content_type} content I want you to generate a script from, source identifier is {source_identifier}: " + content},
            ],
            response_model=response_model,
            max_retries=3
        )
        logger.warning(f"Number input_token: {raw.usage_metadata.prompt_token_count}")
        result = reconstruct_script(response)
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise ValueError(f"The model failed the script generation: {e}")
    
    return result


def _generate_overview_groq(
    content: str, 
    content_type: Literal["research", "tutorial", "general"],
    source_identifier: str
) -> str:
    """Generate overview using Groq."""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        raise ValueError("You need to set the GROQ_API_KEY environment variable.")

    # Select appropriate prompt based on content type
    if content_type == "research":
        system_prompt = RESEARCH_OVERVIEW_PROMPT
    elif content_type == "tutorial":
        system_prompt = TUTORIAL_OVERVIEW_PROMPT
    else:  # general
        system_prompt = GENERAL_OVERVIEW_PROMPT

    groq_client = instructor.from_groq(
        Groq(api_key=GROQ_API_KEY),
        mode=instructor.Mode.JSON_SCHEMA,
        hooks=create_logging_hooks("groq"),
    )
    
    # Select appropriate response model based on content type
    if content_type == "research":
        response_model = generate_model_with_context_check(source_identifier, content)
    elif content_type == "tutorial":
        response_model = generate_tutorial_model_with_context_check(source_identifier, content)
    else:  # general
        response_model = generate_general_model_with_context_check(source_identifier, content)

    response, raw = groq_client.chat.completions.create_with_completion(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the {content_type} content I want you to generate a script from, source identifier is {source_identifier}: " + content},
        ],
        response_model=response_model,
        temperature=0,
        max_retries=3
    )

    try:
        result = reconstruct_script(response)
    except Exception as e:
        logger.error(f"Script reconstruction failed: {e}")
        raise ValueError(f"The model failed the script generation: {e}")
    
    return result


def generate_research_overview(
    markdown: str, 
    paper_id: str,
    method: Literal["openai", "gemini", "groq", "openrouter"] = "openrouter"
) -> str:
    """
    Generate research overview using existing research prompts.
    
    Args:
        markdown: The research paper content in markdown format
        paper_id: The paper ID (for arXiv papers) or source identifier
        method: The AI provider to use for generation
        
    Returns:
        Generated research overview script
        
    Requirements: 5.1, 5.2
    """
    logger.info(f"Generating research overview for paper {paper_id} using {method}")
    
    if method == "openai":
        return _generate_overview_openai(markdown, "research", paper_id)
    elif method == "openrouter":
        return _generate_overview_openrouter(markdown, "research", paper_id)
    elif method == "gemini":
        return _generate_overview_gemini(markdown, "research", paper_id)
    elif method == "groq":
        return _generate_overview_groq(markdown, "research", paper_id)
    else:
        raise ValueError(f"Invalid method: {method}. Choose from 'openai', 'gemini', 'groq', 'openrouter'")


def generate_tutorial_overview(
    markdown: str, 
    url: str,
    method: Literal["openai", "gemini", "groq", "openrouter"] = "openrouter"
) -> str:
    """
    Generate tutorial overview with learning-focused prompts.
    
    Args:
        markdown: The tutorial content in markdown format
        url: The source URL of the tutorial
        method: The AI provider to use for generation
        
    Returns:
        Generated tutorial overview script
        
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    logger.info(f"Generating tutorial overview for URL {url} using {method}")
    
    if method == "openai":
        return _generate_overview_openai(markdown, "tutorial", "tutorial_content")
    elif method == "openrouter":
        return _generate_overview_openrouter(markdown, "tutorial", "tutorial_content")
    elif method == "gemini":
        return _generate_overview_gemini(markdown, "tutorial", "tutorial_content")
    elif method == "groq":
        return _generate_overview_groq(markdown, "tutorial", "tutorial_content")
    else:
        raise ValueError(f"Invalid method: {method}. Choose from 'openai', 'gemini', 'groq', 'openrouter'")


def generate_general_overview(
    markdown: str, 
    url: str,
    method: Literal["openai", "gemini", "groq", "openrouter"] = "openrouter"
) -> str:
    """
    Generate general overview with key-points-focused prompts.
    
    Args:
        markdown: The general content in markdown format
        url: The source URL of the content
        method: The AI provider to use for generation
        
    Returns:
        Generated general overview script
        
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    logger.info(f"Generating general overview for URL {url} using {method}")
    
    if method == "openai":
        return _generate_overview_openai(markdown, "general", "general_content")
    elif method == "openrouter":
        return _generate_overview_openrouter(markdown, "general", "general_content")
    elif method == "gemini":
        return _generate_overview_gemini(markdown, "general", "general_content")
    elif method == "groq":
        return _generate_overview_groq(markdown, "general", "general_content")
    else:
        raise ValueError(f"Invalid method: {method}. Choose from 'openai', 'gemini', 'groq', 'openrouter'")


def generate_overview_by_type(
    content_type: Literal["research", "tutorial", "general"],
    markdown: str,
    source_identifier: str,
    method: Literal["openai", "gemini", "groq", "openrouter"] = "openrouter"
) -> str:
    """
    Generate overview based on content type.
    
    Args:
        content_type: The type of content (research, tutorial, general)
        markdown: The content in markdown format
        source_identifier: Paper ID for research content, URL for others
        method: The AI provider to use for generation
        
    Returns:
        Generated overview script
    """
    if content_type == "research":
        return generate_research_overview(markdown, source_identifier, method)
    elif content_type == "tutorial":
        return generate_tutorial_overview(markdown, source_identifier, method)
    elif content_type == "general":
        return generate_general_overview(markdown, source_identifier, method)
    else:
        raise ValueError(f"Invalid content_type: {content_type}. Choose from 'research', 'tutorial', 'general'")