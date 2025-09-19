import gradio as gr
import logging
from backend.main import (
    generate_paper,
    generate_script,
    generate_assets,
    generate_video,
)
from backend.utils.url_processor import (
    process_url_input,
    is_arxiv_paper_id,
    validate_url,
    is_firecrawl_available,
    process_url_with_firecrawl
)
from backend.utils.content_classifier import classify_content, is_openrouter_available
from pathlib import Path
import tempfile
import shutil
import dotenv
import os
import time
import re

dotenv.load_dotenv()
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

DEFAULT_METHOD_PAPER = "arxiv_html"
DEFAULT_METHOD_SCRIPT = "openrouter"
DEFAULT_METHOD_AUDIO = "kokoro"
DEFAULT_PAPER_ID = "2404.02905"
DEFAULT_URL = "https://arxiv.org/abs/2404.02905"

VIDEO_DIR = Path("generated_videos")
VIDEO_DIR.mkdir(exist_ok=True)

def _status_working(message: str) -> str:
    """Return HTML for a working status with spinner."""
    return f'<div class="status working"><span class="spinner"></span>{message}</div>'


def _status_done(message: str) -> str:
    """Return HTML for a success status."""
    return f'<div class="status done">✅ {message}</div>'


def _status_error(message: str) -> str:
    """Return HTML for an error status."""
    return f'<div class="status error">❌ {message}</div>'


def detect_input_type(input_str: str) -> tuple[str, str]:
    """
    Detect if input is an arXiv ID, URL, or invalid.
    
    Args:
        input_str: User input string
        
    Returns:
        tuple: (input_type, validation_message) where input_type is 'arxiv_id', 'url', or 'invalid'
    """
    if not input_str or not input_str.strip():
        return "invalid", "Input is empty"
    
    input_str = input_str.strip()
    
    # Check if it's an arXiv paper ID
    if is_arxiv_paper_id(input_str):
        return "arxiv_id", f"✅ Valid arXiv paper ID: {input_str}"
    
    # Check if it's a URL
    if validate_url(input_str):
        result = process_url_input(input_str)
        if result.is_arxiv and result.paper_id:
            return "arxiv_url", f"✅ Valid arXiv URL (Paper ID: {result.paper_id})"
        else:
            return "url", f"✅ Valid URL - will use Firecrawl for processing"
    
    return "invalid", "❌ Invalid input - please enter a valid arXiv ID or URL"


def process_url_for_gradio(input_str: str) -> tuple[bool, str, str, str, str]:
    """
    Process URL input for Gradio interface.
    
    Args:
        input_str: User input (arXiv ID or URL)
        
    Returns:
        tuple: (success, content_type, processing_method, markdown_content, error_message)
    """
    try:
        input_type, validation_msg = detect_input_type(input_str)
        
        if input_type == "invalid":
            return False, "", "", "", validation_msg
        
        # Process arXiv inputs using existing logic
        if input_type in ["arxiv_id", "arxiv_url"]:
            result = process_url_input(input_str)
            if result.is_arxiv and result.paper_id:
                # Use existing arXiv processing
                try:
                    markdown_content = generate_paper(DEFAULT_METHOD_PAPER, result.paper_id)
                    # Classify the content
                    if is_openrouter_available():
                        classification = classify_content(markdown_content)
                        content_type = classification.content_type
                    else:
                        content_type = "research"  # Default for arXiv papers
                    
                    return True, content_type, "arxiv", markdown_content, ""
                except Exception as e:
                    return False, "", "", "", f"Failed to process arXiv paper: {str(e)}"
            else:
                return False, "", "", "", "Failed to extract paper ID from arXiv URL"
        
        # Process general URLs using Firecrawl
        elif input_type == "url":
            if not is_firecrawl_available():
                return False, "", "", "", "Firecrawl is not available. Please check FIRECRAWL_API_KEY environment variable."
            
            firecrawl_result = process_url_with_firecrawl(input_str)
            if not firecrawl_result.success:
                return False, "", "", "", f"Failed to process URL: {firecrawl_result.error_message}"
            
            # Classify the content
            if is_openrouter_available():
                classification = classify_content(firecrawl_result.markdown_content)
                content_type = classification.content_type
            else:
                content_type = "general"  # Default fallback
            
            return True, content_type, "firecrawl", firecrawl_result.markdown_content, ""
        
        return False, "", "", "", "Unknown input type"
        
    except Exception as e:
        logger.error(f"Error processing URL in Gradio: {str(e)}")
        return False, "", "", "", f"Processing error: {str(e)}"


def get_content_type_display(content_type: str, confidence: float = 0.0) -> str:
    """
    Generate HTML display for content type with appropriate styling.
    
    Args:
        content_type: The detected content type
        confidence: Confidence score (0.0-1.0)
        
    Returns:
        HTML string for content type display
    """
    if not content_type:
        return ""
    
    type_colors = {
        "research": "#3b82f6",  # Blue
        "tutorial": "#10b981",  # Green  
        "general": "#6b7280"    # Gray
    }
    
    type_icons = {
        "research": "🔬",
        "tutorial": "📚", 
        "general": "📄"
    }
    
    color = type_colors.get(content_type, "#6b7280")
    icon = type_icons.get(content_type, "📄")
    
    confidence_text = f" ({confidence:.1%} confidence)" if confidence > 0 else ""
    
    return f"""
    <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; 
                background: {color}20; border: 1px solid {color}40; border-radius: 8px; margin: 4px 0;">
        <span style="font-size: 18px;">{icon}</span>
        <span style="color: {color}; font-weight: 600; text-transform: capitalize;">
            {content_type} Content{confidence_text}
        </span>
    </div>
    """


def get_processing_method_display(method: str, source_url: str = "") -> str:
    """
    Generate HTML display for processing method.
    
    Args:
        method: Processing method ("arxiv" or "firecrawl")
        source_url: Source URL for attribution
        
    Returns:
        HTML string for processing method display
    """
    if not method:
        return ""
    
    method_info = {
        "arxiv": {
            "name": "arXiv Processing",
            "icon": "🎓",
            "color": "#f59e0b",
            "description": "Using optimized arXiv paper processing"
        },
        "firecrawl": {
            "name": "Firecrawl Processing", 
            "icon": "🌐",
            "color": "#8b5cf6",
            "description": "Using Firecrawl for web content extraction"
        }
    }
    
    info = method_info.get(method, method_info["firecrawl"])
    
    source_display = ""
    if source_url:
        # Truncate long URLs for display
        display_url = source_url if len(source_url) <= 50 else source_url[:47] + "..."
        source_display = f"<br><small style='color: #6b7280;'>Source: {display_url}</small>"
    
    return f"""
    <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px;
                background: {info['color']}20; border: 1px solid {info['color']}40; 
                border-radius: 8px; margin: 4px 0;">
        <span style="font-size: 18px;">{info['icon']}</span>
        <div>
            <span style="color: {info['color']}; font-weight: 600;">{info['name']}</span>
            <br><small style="color: #6b7280;">{info['description']}</small>
            {source_display}
        </div>
    </div>
    """

def process_and_generate_video(
    input_source: str,
    method_paper,
    url_or_paper_id,
    method_script,
    method_audio,
    pdf_file,
    content_type_override,
    api_base_url=None,
):
    """Processes the entire pipeline and generates the video with URL support."""
    status = _status_working("Starting the pipeline...")
    yield gr.update(value=status), None  # Update status, no video yet

    temp_dir = None
    try:
        # Validate inputs based on selected source
        if input_source == "Upload PDF":
            if not pdf_file:
                status = "Error: Please upload a PDF file or switch to URL/ArXiv ID."
                yield gr.update(value=status), None
                return
            # When using PDF, we override method/paper_id internally
            use_pdf = True
            paper_markdown = None
            content_type = content_type_override if content_type_override else "research"
        elif input_source == "URL/ArXiv ID":
            use_pdf = False
            if not url_or_paper_id or str(url_or_paper_id).strip() == "":
                status = "Error: Please provide a valid URL or ArXiv paper ID."
                yield gr.update(value=status), None
                return
            
            # Process URL or arXiv ID
            status = _status_working("Processing URL/ArXiv ID...")
            yield gr.update(value=status), None
            
            success, detected_content_type, processing_method, paper_markdown, error_msg = process_url_for_gradio(url_or_paper_id)
            if not success:
                status = _status_error(error_msg)
                yield gr.update(value=status), None
                return
            
            # Use override if provided, otherwise use detected type
            content_type = content_type_override if content_type_override else detected_content_type
            logger.info(f"Content processed via {processing_method}, classified as {content_type}")
        else:
            status = "Error: Invalid input source selected."
            yield gr.update(value=status), None
            return

        # Validate local LLM base URL when using local method
        if method_script == "local" and not api_base_url:
            status = "Error: Please provide a Custom LLM API Base URL for the 'local' script method."
            yield gr.update(value=status), None
            return

        # 1. Generate Paper Markdown (if not already done)
        if use_pdf:
            status = _status_working("Generating paper markdown from PDF...")
            yield gr.update(value=status), None
            paper_markdown = generate_paper("pdf", "paper_id", pdf_path=pdf_file)
        elif not paper_markdown:
            # This shouldn't happen with URL processing, but fallback just in case
            status = _status_working("Generating paper markdown...")
            yield gr.update(value=status), None
            # Extract paper ID for arXiv processing
            result = process_url_input(url_or_paper_id)
            if result.is_arxiv and result.paper_id:
                paper_markdown = generate_paper(method_paper, result.paper_id)
            else:
                status = _status_error("Unable to process content - no markdown available")
                yield gr.update(value=status), None
                return
        
        logger.info("Paper markdown generated successfully.")
        
        # 2. Generate Script with content type awareness
        if use_pdf:
            status = _status_working("Generating script from PDF markdown...")
            yield gr.update(value=status), None
            script = generate_script(
                method_script, paper_markdown, "paper_id", api_base_url, 
                from_pdf=True, content_type=content_type
            )
        else:
            status = _status_working(f"Generating {content_type} script from markdown...")
            yield gr.update(value=status), None
            # For URL processing, use URL as identifier
            identifier = url_or_paper_id if input_source == "URL/ArXiv ID" else "paper_id"
            script = generate_script(
                method_script, paper_markdown, identifier, api_base_url,
                content_type=content_type
            )
        logger.info("Script generated successfully.")

        # 3. Create temporary directory for assets
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        mp3_output = temp_path / "audio.wav"
        srt_output = temp_path / "subtitles.srt"
        rich_output = temp_path / "rich.json"
        input_dir = temp_path
        output_video = temp_path / "output.mp4"

        # 4. Generate Assets
        status = _status_working("Generating audio, subtitles, and rich content assets...")
        yield gr.update(value=status), None
        generate_assets(
            script,
            method_audio,
            mp3_output=str(mp3_output),
            srt_output=str(srt_output),
            rich_output=str(rich_output),
        )
        logger.info("Assets generated successfully.")

        # 5. Generate Video
        status = _status_working("Generating video...")
        yield gr.update(value=status), None
        generate_video(input_dir, output_video)
        logger.info("Video generated successfully.")

        # 6. Move video to the permanent directory
        status = _status_working("Finalizing and saving video...")
        yield gr.update(value=status), None
        
        # Create a safe filename from the input
        if use_pdf:
            safe_name = "pdf_upload"
        else:
            # Extract a safe identifier from URL or paper ID
            result = process_url_input(url_or_paper_id)
            if result.is_arxiv and result.paper_id:
                safe_name = result.paper_id
            else:
                # Create safe name from URL
                safe_name = re.sub(r'[^\w\-_.]', '_', url_or_paper_id)[:50]
        
        final_video_path = VIDEO_DIR / f"video_{safe_name}_{int(time.time())}.mp4"
        shutil.move(str(output_video), str(final_video_path))
        logger.info(f"Video saved to {final_video_path}")

        status = _status_done(f"Pipeline completed! Video saved at: {final_video_path}")
        yield gr.update(value=status), str(final_video_path)  # Return video path as video_output

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        status = _status_error(f"Error: {e}. Check logs for details.")
        yield gr.update(value=status), None  # Return error status, no video

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)


def _toggle_source(choice: str):
    """Toggle visibility and interactivity of inputs based on source choice."""
    if choice == "URL/ArXiv ID":
        return (
            gr.update(visible=True),   # url_or_paper_id_input
            gr.update(visible=False),  # pdf_file_input
            gr.update(interactive=True),  # method_paper_input
            gr.update(visible=True),   # input_validation_display
            gr.update(visible=False),  # content_type_display
            gr.update(visible=False),  # processing_method_display
            gr.update(visible=True),   # process_url_button
            gr.update(visible=False),  # content_type_override
        )
    else:  # Upload PDF
        return (
            gr.update(visible=False),  # url_or_paper_id_input
            gr.update(visible=True),   # pdf_file_input
            gr.update(interactive=False),  # method_paper_input
            gr.update(visible=False),  # input_validation_display
            gr.update(visible=False),  # content_type_display
            gr.update(visible=False),  # processing_method_display
            gr.update(visible=False),  # process_url_button
            gr.update(visible=True),   # content_type_override
        )


def _reset_fields():
    """Return default values to reset the UI."""
    return (
        "URL/ArXiv ID",  # input_source
        DEFAULT_METHOD_PAPER,  # method_paper_input
        DEFAULT_URL,  # url_or_paper_id_input
        DEFAULT_METHOD_SCRIPT,  # method_script_input
        DEFAULT_METHOD_AUDIO,  # method_audio_input
        None,  # pdf_file_input
        None,  # content_type_override
        None,  # api_base_url
        gr.update(value="Idle..."),  # status_output
        None,  # video_output
        "",  # input_validation_display
        "",  # content_type_display
        "",  # processing_method_display
    )


# Define Gradio interface
CUSTOM_CSS = """
:root {
  --arx-grad-1: #0ea5e9;
  --arx-grad-2: #8b5cf6;
  --arx-grad-3: #ec4899;
}

body, #root, .gradio-container {
  background:
    radial-gradient(1200px 800px at 10% 10%, rgba(14,165,233,.12), transparent 40%),
    radial-gradient(1000px 600px at 90% 30%, rgba(139,92,246,.12), transparent 50%),
    radial-gradient(800px 600px at 30% 90%, rgba(236,72,153,.12), transparent 50%);
  animation: bgFloat 16s ease-in-out infinite alternate;
}

@keyframes bgFloat {
  0% { background-position: 0 0, 0 0, 0 0; }
  100% { background-position: 30px -30px, -20px 20px, 25px -15px; }
}

#arx-header {
  text-align:center; font-size: 32px; font-weight: 800; margin: 8px 0 4px;
  background: linear-gradient(90deg, var(--arx-grad-1), var(--arx-grad-2), var(--arx-grad-3));
  -webkit-background-clip: text; background-clip:text; color: transparent; letter-spacing: .5px;
}

#arx-sub {text-align:center; color:#a3a3a3; margin: 0 0 18px;}

#controls, #output-panel {
  backdrop-filter: blur(8px);
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,.12);
}

#controls {gap: 12px;}

#actions .gr-button {
  height:48px; font-weight:700; border-radius: 12px;
  transition: transform .15s ease, box-shadow .2s ease, filter .2s ease;
}

#actions .gr-button, #actions .gr-button-primary {
  background: linear-gradient(135deg, var(--arx-grad-1), var(--arx-grad-2));
  color: #fff; border: none;
}

#actions .gr-button:hover {
  transform: translateY(-1px); filter: brightness(1.05);
  box-shadow: 0 10px 20px rgba(139,92,246,.25);
}

#actions .gr-button:active { transform: translateY(0); filter: brightness(.98); box-shadow: none; }

/* Content type and processing method displays */
.content-type-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  margin: 4px 0;
  font-weight: 600;
}

.processing-method-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  margin: 4px 0;
}

/* URL processing button styling */
.gr-button[variant="secondary"] {
  background: linear-gradient(135deg, rgba(139,92,246,.2), rgba(14,165,233,.2));
  border: 1px solid rgba(139,92,246,.3);
  color: #8b5cf6;
  font-weight: 600;
}

.gr-button[variant="secondary"]:hover {
  background: linear-gradient(135deg, rgba(139,92,246,.3), rgba(14,165,233,.3));
  transform: translateY(-1px);
}

/* Content type options styling */
.gr-group {
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.05);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
}

/* Input validation styling */
.input-validation {
  padding: 8px;
  margin: 4px 0;
  border-radius: 6px;
  font-size: 14px;
}

.input-validation.valid {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.input-validation.invalid {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

#status-title {margin-bottom:8px;}
#status {min-height:64px; opacity:.98; padding: 12px 14px; border-radius: 12px; background: rgba(17,24,39,.5); border: 1px solid rgba(255,255,255,.06)}

.status { display:flex; align-items:center; gap: 10px; font-weight: 600; }
.status .spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
.status.done { color: #a7f3d0; }
.status.error { color: #fecaca; }

@keyframes spin { to { transform: rotate(360deg); } }

.gr-example { border-radius: 10px; }

/* Accordion styling */
.gr-accordion {
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.05);
  border-radius: 8px;
  margin: 8px 0;
}

/* Radio button styling for content types */
.gr-radio {
  background: rgba(255,255,255,.02);
  border-radius: 6px;
  padding: 8px;
}

/* Checkbox styling */
.gr-checkbox {
  background: rgba(255,255,255,.02);
  border-radius: 4px;
  padding: 4px;
}
"""

with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
    gr.HTML("""
    <div id="arx-header">ArXFlix Universal Content Processor</div>
    <div id="arx-sub">Turn any URL, arXiv paper, or PDF into engaging short videos</div>
    """)

    with gr.Row():
        with gr.Column(scale=1, min_width=360):
            with gr.Group(elem_id="controls"):
                input_source = gr.Radio(
                    ["URL/ArXiv ID", "Upload PDF"],
                    value="URL/ArXiv ID",
                    label="Content Source",
                    info="Enter any URL or arXiv paper ID, or upload a PDF to process",
                )

                # URL/ArXiv ID input with smart detection
                url_or_paper_id_input = gr.Textbox(
                    label="URL or arXiv Paper ID",
                    value=DEFAULT_URL,
                    placeholder="e.g. https://arxiv.org/abs/2404.02905 or 2404.02905 or any URL",
                    info="Supports arXiv papers, tutorials, articles, and more"
                )

                # Real-time input validation display
                input_validation_display = gr.HTML(
                    value="",
                    visible=True
                )

                # Process URL button for content analysis
                process_url_button = gr.Button(
                    "🔍 Analyze Content", 
                    variant="secondary",
                    visible=True
                )

                # Content type and processing method displays
                content_type_display = gr.HTML(
                    value="",
                    visible=False
                )
                
                processing_method_display = gr.HTML(
                    value="",
                    visible=False
                )

                pdf_file_input = gr.File(
                    label="Upload PDF",
                    file_types=[".pdf"],
                    type="filepath",
                    visible=False,
                )

            # Content type specific options
            with gr.Accordion("Content Type Options", open=False):
                content_type_override = gr.Radio(
                    choices=["research", "tutorial", "general"],
                    label="Override Content Type (optional)",
                    info="Override automatic classification if needed",
                    visible=False
                )
                
                # Research content options
                research_options = gr.Group(visible=False)
                with research_options:
                    gr.Markdown("### Research Paper Options")
                    technical_level = gr.Radio(
                        choices=["beginner", "intermediate", "advanced"],
                        value="intermediate",
                        label="Technical Level",
                        info="Adjust explanation complexity"
                    )
                
                # Tutorial content options  
                tutorial_options = gr.Group(visible=False)
                with tutorial_options:
                    gr.Markdown("### Tutorial Content Options")
                    include_code_examples = gr.Checkbox(
                        value=True,
                        label="Highlight Code Examples",
                        info="Emphasize code snippets and examples"
                    )
                    step_by_step_focus = gr.Checkbox(
                        value=True,
                        label="Step-by-Step Focus",
                        info="Structure content as clear steps"
                    )
                
                # General content options
                general_options = gr.Group(visible=False)
                with general_options:
                    gr.Markdown("### General Content Options")
                    focus_on_key_points = gr.Checkbox(
                        value=True,
                        label="Focus on Key Takeaways",
                        info="Emphasize main points and conclusions"
                    )
                    include_context = gr.Checkbox(
                        value=True,
                        label="Include Background Context",
                        info="Provide relevant background information"
                    )

            with gr.Accordion("Advanced Settings", open=False):
                method_paper_input = gr.Dropdown(
                    ["arxiv_gpt", "arxiv_html"],
                    label="arXiv Processing Method",
                    value=DEFAULT_METHOD_PAPER,
                    info="How to extract content from arXiv papers",
                )

                api_base_url = gr.Textbox(
                    label="Custom LLM API Base URL (optional)",
                    value=None,
                    placeholder="http(s)://host:port/v1 (for local/open-source inference)",
                    visible=False,
                )

            method_script_input = gr.Dropdown(
                ["openai", "local", "gemini", "openrouter", "groq"],
                label="Script Generation Method",
                value=DEFAULT_METHOD_SCRIPT,
                info="Choose the AI provider for script generation"
            )
            method_audio_input = gr.Dropdown(
                ["elevenlabs", "lmnt", "kokoro"],
                label="Audio Generation Method",
                value=DEFAULT_METHOD_AUDIO,
                info="Choose the voice synthesis provider"
            )

            with gr.Row(elem_id="actions"):
                generate_button = gr.Button("Generate Video 🚀", variant="primary")
                reset_button = gr.Button("Reset ↺")

            # Enhanced examples with different content types
            gr.Examples(
                examples=[
                    ["URL/ArXiv ID", "https://arxiv.org/abs/2404.02905", "openrouter", "kokoro"],
                    ["URL/ArXiv ID", "2506.05301", "openrouter", "kokoro"],
                    ["URL/ArXiv ID", "https://docs.python.org/3/tutorial/", "openrouter", "kokoro"],
                ],
                inputs=[input_source, url_or_paper_id_input, method_script_input, method_audio_input],
                label="Examples",
            )

        with gr.Column(scale=1):
            with gr.Group(elem_id="output-panel"):
                gr.Markdown("### Progress", elem_id="status-title")
                status_output = gr.Markdown("Idle...", elem_id="status")
                video_output = gr.Video(label="Generated Video")

    # Helper functions for event handlers
    def handle_input_change(input_str: str):
        """Handle real-time input validation and display."""
        if not input_str or not input_str.strip():
            return gr.update(value="")
        
        input_type, validation_msg = detect_input_type(input_str)
        return gr.update(value=f"<div style='padding: 8px; margin: 4px 0;'>{validation_msg}</div>")

    def handle_url_processing(input_str: str):
        """Handle URL processing and content analysis."""
        if not input_str or not input_str.strip():
            return [
                gr.update(value="<div style='color: #ef4444;'>Please enter a URL or arXiv ID</div>"),
                gr.update(value="", visible=False),
                gr.update(value="", visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            ]
        
        try:
            success, content_type, processing_method, markdown_content, error_msg = process_url_for_gradio(input_str)
            
            if not success:
                return [
                    gr.update(value=f"<div style='color: #ef4444;'>❌ {error_msg}</div>"),
                    gr.update(value="", visible=False),
                    gr.update(value="", visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False)
                ]
            
            # Get classification confidence if available
            confidence = 0.8  # Default confidence for display
            if is_openrouter_available() and markdown_content:
                try:
                    classification = classify_content(markdown_content)
                    confidence = classification.confidence_score
                except:
                    pass
            
            content_type_html = get_content_type_display(content_type, confidence)
            processing_method_html = get_processing_method_display(processing_method, input_str)
            
            # Show content type specific options
            show_research = content_type == "research"
            show_tutorial = content_type == "tutorial" 
            show_general = content_type == "general"
            
            return [
                gr.update(value="<div style='color: #10b981;'>✅ Content processed successfully!</div>"),
                gr.update(value=content_type_html, visible=True),
                gr.update(value=processing_method_html, visible=True),
                gr.update(visible=show_research),
                gr.update(visible=show_tutorial),
                gr.update(visible=show_general),
                gr.update(visible=True)  # content_type_override
            ]
            
        except Exception as e:
            logger.error(f"Error in URL processing handler: {str(e)}")
            return [
                gr.update(value=f"<div style='color: #ef4444;'>❌ Processing error: {str(e)}</div>"),
                gr.update(value="", visible=False),
                gr.update(value="", visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            ]

    def handle_content_type_change(content_type: str):
        """Handle content type override changes."""
        if not content_type:
            return [
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            ]
        
        return [
            gr.update(visible=content_type == "research"),
            gr.update(visible=content_type == "tutorial"),
            gr.update(visible=content_type == "general")
        ]

    # Wire source toggle
    input_source.change(
        _toggle_source,
        inputs=[input_source],
        outputs=[
            url_or_paper_id_input, 
            pdf_file_input, 
            method_paper_input,
            input_validation_display,
            content_type_display,
            processing_method_display,
            process_url_button,
            content_type_override
        ],
    )

    # Real-time input validation
    url_or_paper_id_input.change(
        handle_input_change,
        inputs=[url_or_paper_id_input],
        outputs=[input_validation_display]
    )

    # URL processing handler
    process_url_button.click(
        handle_url_processing,
        inputs=[url_or_paper_id_input],
        outputs=[
            input_validation_display,
            content_type_display,
            processing_method_display,
            research_options,
            tutorial_options,
            general_options,
            content_type_override
        ]
    )

    # Content type override handler
    content_type_override.change(
        handle_content_type_change,
        inputs=[content_type_override],
        outputs=[research_options, tutorial_options, general_options]
    )

    # Generate handler
    generate_button.click(
        process_and_generate_video,
        inputs=[
            input_source,
            method_paper_input,
            url_or_paper_id_input,
            method_script_input,
            method_audio_input,
            pdf_file_input,
            content_type_override,
            api_base_url,
        ],
        outputs=[status_output, video_output],
    )

    def _toggle_api_base(method: str):
        """Show API Base URL only for local method."""
        return gr.update(visible=(method == "local"))

    method_script_input.change(
        _toggle_api_base,
        inputs=[method_script_input],
        outputs=[api_base_url],
    )

    # Reset handler
    reset_button.click(
        _reset_fields,
        inputs=None,
        outputs=[
            input_source,
            method_paper_input,
            url_or_paper_id_input,
            method_script_input,
            method_audio_input,
            pdf_file_input,
            content_type_override,
            api_base_url,
            status_output,
            video_output,
            input_validation_display,
            content_type_display,
            processing_method_display,
        ],
    )

if __name__ == "__main__":
    demo.queue().launch(share=True)