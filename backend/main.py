from pathlib import Path
import logging
import os
import tempfile
from typing import Literal, Optional, Dict, Any
from dotenv import load_dotenv
import typer
import fastapi
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time
import traceback

from backend.utils import (
    process_video,
)
from backend.utils import (
    generate_audio_and_caption,
    fill_rich_content_time,
    export_mp3,
    export_srt,
    export_rich_content_json,
)
from backend.utils import process_article
from backend.utils import process_script
from backend.type import Text, RichContent

# Import new URL processing utilities
from backend.utils.url_processor import (
    process_url_input,
    process_url_with_firecrawl,
    process_any_url,
    is_arxiv_url,
    extract_arxiv_paper_id,
    URLProcessingResult,
    FirecrawlResult,
    FirecrawlError
)
from backend.utils.content_classifier import (
    classify_content,
    ContentClassification
)
from backend.utils.overview_generators import (
    generate_overview_by_type
)

# Load logger
logger = logging.getLogger(__name__)

# Configure logging for better error tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load .env file
load_dotenv()


# Error handling utilities
def handle_processing_error(error: Exception, context: str = "processing") -> "ErrorResponse":
    """
    Standardized error response format for consistent error handling.
    
    Requirements: 8.1, 8.3, 8.4
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Log the error with context
    logger.error(f"Error in {context}: {error_message}")
    logger.error(f"Error type: {error_type}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Determine error details based on error type
    details = {}
    if hasattr(error, 'details'):
        details = error.details
    elif isinstance(error, FirecrawlError):
        details = {
            "error_type": getattr(error, 'error_type', 'unknown'),
            "firecrawl_details": getattr(error, 'details', {})
        }
    
    return ErrorResponse(
        error_type=error_type,
        error_message=error_message,
        details=details if details else None
    )


def log_api_request(endpoint: str, request_data: Dict[str, Any]) -> None:
    """
    Log API request details for monitoring and debugging.
    
    Requirements: 8.1, 8.4
    """
    # Sanitize sensitive data
    sanitized_data = request_data.copy()
    if 'content' in sanitized_data and len(sanitized_data['content']) > 200:
        sanitized_data['content'] = sanitized_data['content'][:200] + "... (truncated)"
    
    logger.info(f"API Request to {endpoint}: {sanitized_data}")


def log_api_response(endpoint: str, success: bool, processing_time: float, error: str = None) -> None:
    """
    Log API response details for monitoring and debugging.
    
    Requirements: 8.1, 8.4
    """
    status = "SUCCESS" if success else "FAILED"
    log_msg = f"API Response from {endpoint}: {status} (took {processing_time:.2f}s)"
    
    if error:
        log_msg += f" - Error: {error}"
        logger.error(log_msg)
    else:
        logger.info(log_msg)

# Create CLI and API
cli = typer.Typer()
api = fastapi.FastAPI()


# Pydantic models for new API endpoints
class URLProcessRequest(BaseModel):
    """Request model for URL processing endpoint"""
    url: str = Field(..., description="The URL to process", min_length=1)


class URLProcessResponse(BaseModel):
    """Response model for URL processing endpoint"""
    success: bool = Field(..., description="Whether the processing was successful")
    markdown_content: Optional[str] = Field(None, description="Extracted markdown content")
    content_type: Optional[str] = Field(None, description="Classified content type (research, tutorial, general)")
    source_type: Optional[str] = Field(None, description="Processing method used (arxiv, firecrawl)")
    paper_id: Optional[str] = Field(None, description="ArXiv paper ID if applicable")
    source_url: str = Field(..., description="Original source URL")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    confidence_score: Optional[float] = Field(None, description="Classification confidence score")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class GenerateOverviewRequest(BaseModel):
    """Request model for overview generation endpoint"""
    content: str = Field(..., description="Markdown content to generate overview from", min_length=10)
    content_type: Literal["research", "tutorial", "general"] = Field(..., description="Type of content")
    source_identifier: str = Field(..., description="Paper ID for research content, URL for others")
    method: Literal["openai", "gemini", "groq", "openrouter"] = Field(default="openrouter", description="AI provider to use")


class GenerateOverviewResponse(BaseModel):
    """Response model for overview generation endpoint"""
    success: bool = Field(..., description="Whether the generation was successful")
    script: Optional[str] = Field(None, description="Generated script content")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = Field(default=False, description="Always false for error responses")
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Detailed error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Add CORS middleware to API
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@cli.command("generate_paper")
@api.get("/generate_paper/")
def generate_paper(method: Literal["arxiv_gpt", "arxiv_html", "pdf"], paper_id: str = None, pdf_path: str = None, url: str = None) -> str:
    """Generate paper markdown using ArxivGPT, ArxivHTML api, or URL processing

    Parameters
    ----------
    method : "arxiv_gpt" | "arxiv_html" | "pdf"
        The method to generate paper markdown
    paper_id : str, optional
        The paper id to generate markdown (for arXiv processing)
    pdf_path : str, optional
        Path to PDF file (for PDF processing)
    url : str, optional
        URL to process (for URL processing)

    Returns
    -------
    str
        The paper markdown
    """
    try:
        # Handle URL input - route to appropriate processor
        if url:
            logger.info(f"Processing URL: {url}")
            
            # Check if it's an arXiv URL
            if is_arxiv_url(url):
                extracted_paper_id = extract_arxiv_paper_id(url)
                if extracted_paper_id:
                    logger.info(f"Detected arXiv URL, extracting paper ID: {extracted_paper_id}")
                    return process_article(method, extracted_paper_id, pdf_path)
                else:
                    raise ValueError(f"Could not extract paper ID from arXiv URL: {url}")
            else:
                # For non-arXiv URLs, use Firecrawl
                result = process_url_with_firecrawl(url)
                if not result.success:
                    raise ValueError(f"Failed to process URL: {result.error_message}, {traceback.format_exc()}")
                return result.markdown_content
        
        # Handle traditional paper_id input
        elif paper_id:
            logger.info(f"Generating paper markdown using method: {method} and paper_id: {paper_id}")
            return process_article(method, paper_id, pdf_path)
        
        else:
            raise ValueError("Either 'paper_id' or 'url' parameter must be provided")
            
    except Exception as e:
        logger.error(f"Error in generate_paper: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)+f"{traceback.format_exc()}")


@cli.command("generate_script")
@api.post("/generate_script/")
def generate_script(method: Literal["openai","local","gemini","openrouter","groq"], paper_markdown: str, paper_id: str, end_point_base_url: str = None, from_pdf: bool = False, content_type: Optional[Literal["research", "tutorial", "general"]] = None) -> str:
    """Generate video script from paper markdown using an LLM with optional content type awareness

    Parameters
    ----------
    method : "openai" | "local" | "gemini" | "openrouter" | "groq"
        The method to generate script
    paper_markdown : str
        The paper markdown
    paper_id : str
        The paper ID or source identifier
    end_point_base_url : str, optional
        Custom endpoint base URL
    from_pdf : bool, optional
        Whether the content is from PDF processing
    content_type : "research" | "tutorial" | "general", optional
        Content type for specialized processing

    Returns
    -------
    str
        The video script
        
    Requirements: 5.1, 5.2, 6.1, 6.2, 7.1, 7.2
    """
    try:
        if from_pdf:
            paper_id = "paper_id"
        
        logger.info(f"Generating script from content using method: {method}")
        
        # Use the enhanced process_script function with content type awareness
        # Default to "research" for backward compatibility if no content_type specified
        effective_content_type = content_type or "research"
        
        logger.info(f"Using content type: {effective_content_type}")
        
        script = process_script(
            method=method,
            paper_markdown=paper_markdown,
            paper_id=paper_id,
            end_point_base_url=end_point_base_url,
            from_pdf=from_pdf,
            content_type=effective_content_type
        )
        
        return script
        
    except Exception as e:
        logger.error(f"Error in generate_script: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)+f"\n{traceback.format_exc()}")


@cli.command("generate_assets")
@api.post("/generate_assets/")
def generate_assets(
    script: str,
    method: Literal["elevenlabs", "lmnt", "kokoro"] = "kokoro",
    mp3_output: str = "public/audio.wav",
    srt_output: str = "public/output.srt",
    rich_output: str = "public/output.json",
) -> float:
    """Generate audio, caption, and rich content assets from script

    Parameters
    ----------
    script : str
        The video script
    method : "elevenlabs" | "lmnt" | "kokoro", optional
        The method to generate audio, by default "kokoro"
    mp3_output : str, optional
        The output mp3 file path, by default "public/audio.wav"
    srt_output : str, optional
        The output srt file path, by default "public/output.srt"
    rich_output : str, optional
        The output rich content json file path, by default "public/output.json

    Returns
    -------
    float
        The total duration of the audio
    """
    logger.info(f"Generating assets from script: {script}")

    # Create a temporary directory
    temp_dir = tempfile.TemporaryDirectory()
    logger.info(f"Created temporary directory: {temp_dir}")

    # Create parent directory for mp3_output, srt_output, and rich_output
    os.makedirs(os.path.dirname(mp3_output), exist_ok=True)
    os.makedirs(os.path.dirname(srt_output), exist_ok=True)
    os.makedirs(os.path.dirname(rich_output), exist_ok=True)

    # Generate audio and caption for each text content
    script_contents = generate_audio_and_caption(method, script)
    # Fill the time for each RichContent
    script_contents = fill_rich_content_time(script_contents)

    # Separate rich content and text content
    rich_content = [c for c in script_contents if isinstance(c, RichContent)]
    text_content = [c for c in script_contents if isinstance(c, Text)]

    # Export mp3
    export_mp3(text_content, mp3_output, offset=0.5)

    # Export srt
    export_srt(mp3_output, srt_output)

    # Export rich content
    export_rich_content_json(rich_content, rich_output)

    # Remove temp_dir
    temp_dir.cleanup()

    total_duration = text_content[-1].end if text_content[-1].end else 0
    return total_duration


@cli.command("generate_video")
@api.post("/generate_video/")
def generate_video(
    input_dir: str,
    output_video: str,
):
    """Generate video from input directory.
    The input directory should contain subtitles.srt, audio.wav, and rich.json files.

    Parameters
    ----------
    input_dir : str
        The input directory containing subtitles.srt, audio.wav, and rich.json
    output_video : str
        Path of the output video
    """
    _input_dir = Path(input_dir)
    _output_video = Path(output_video)

    logger.info(f"Generating video to {_output_video.name} from {_input_dir.name}")

    if not _input_dir.exists() or not _input_dir.is_dir():
        raise FileNotFoundError(f"Input directory {_input_dir} does not exist")

    if not (_input_dir / "subtitles.srt").exists():
        raise FileNotFoundError(f"Subtitles file does not exist in {_input_dir}")
    if not (_input_dir / "audio.wav").exists():
        raise FileNotFoundError(f"Audio file does not exist in {_input_dir}")
    if not (_input_dir / "rich.json").exists():
        raise FileNotFoundError(f"Rich content file does not exist in {_input_dir}")

    process_video(_input_dir, _output_video)


# New API endpoints for URL processing and content-type-aware overview generation

@api.post("/process_url/", response_model=URLProcessResponse)
def process_url_endpoint(request: URLProcessRequest) -> URLProcessResponse:
    """
    Process any URL to extract content and classify it.
    
    This endpoint handles both arXiv URLs (using existing processing) and 
    general URLs (using Firecrawl), then classifies the content type.
    
    Requirements: 8.1, 8.3, 9.1, 9.2
    """
    start_time = time.time()
    
    # Log the incoming request
    log_api_request("/process_url/", {"url": request.url})
    
    try:
        logger.info(f"Processing URL: {request.url}")
        
        # Validate and process the URL input
        url_result = process_url_input(request.url)
        
        if not url_result.is_valid:
            error_msg = url_result.error_message or "Invalid URL"
            log_api_response("/process_url/", False, time.time() - start_time, error_msg)
            return URLProcessResponse(
                success=False,
                source_url=request.url,
                processing_time=time.time() - start_time,
                error_message=error_msg
            )
        
        # Process the URL to get markdown content
        if url_result.is_arxiv:
            # Use existing arXiv processing
            try:
                paper_id = url_result.paper_id
                if not paper_id:
                    # Try to extract from URL if not already extracted
                    paper_id = extract_arxiv_paper_id(request.url)
                
                if not paper_id:
                    raise ValueError("Could not extract paper ID from arXiv URL")
                
                # Use existing arXiv processing (arxiv_html method as default)
                markdown_content = process_article("arxiv_html", paper_id, None)
                source_type = "arxiv"
                
            except Exception as e:
                logger.error(f"ArXiv processing failed: {str(e)}")
                return URLProcessResponse(
                    success=False,
                    source_url=request.url,
                    processing_time=time.time() - start_time,
                    error_message=f"ArXiv processing failed: {str(e)}"
                )
        else:
            # Use Firecrawl for non-arXiv URLs
            try:
                firecrawl_result = process_url_with_firecrawl(request.url)
                
                if not firecrawl_result.success:
                    return URLProcessResponse(
                        success=False,
                        source_url=request.url,
                        processing_time=time.time() - start_time,
                        error_message=firecrawl_result.error_message or "Firecrawl processing failed"
                    )
                
                markdown_content = firecrawl_result.markdown_content
                source_type = "firecrawl"
                paper_id = None
                
            except FirecrawlError as e:
                logger.error(f"Firecrawl error: {str(e)}")
                return URLProcessResponse(
                    success=False,
                    source_url=request.url,
                    processing_time=time.time() - start_time,
                    error_message=f"Firecrawl error: {e.message}"
                )
            except Exception as e:
                logger.error(f"Unexpected error during Firecrawl processing: {str(e)}")
                return URLProcessResponse(
                    success=False,
                    source_url=request.url,
                    processing_time=time.time() - start_time,
                    error_message=f"Processing failed: {str(e)}"
                )
        
        # Classify the content
        try:
            classification = classify_content(markdown_content)
            
            processing_time = time.time() - start_time
            log_api_response("/process_url/", True, processing_time)
            
            return URLProcessResponse(
                success=True,
                markdown_content=markdown_content,
                content_type=classification.content_type,
                source_type=source_type,
                paper_id=paper_id,
                source_url=request.url,
                processing_time=processing_time,
                confidence_score=classification.confidence_score,
                metadata={
                    "features": classification.features,
                    "reasoning": classification.reasoning
                }
            )
            
        except Exception as e:
            logger.error(f"Content classification failed: {str(e)}")
            processing_time = time.time() - start_time
            
            # Return success with content but no classification
            log_api_response("/process_url/", True, processing_time, f"Classification failed: {str(e)}")
            
            return URLProcessResponse(
                success=True,
                markdown_content=markdown_content,
                content_type="general",  # Default fallback
                source_type=source_type,
                paper_id=paper_id,
                source_url=request.url,
                processing_time=processing_time,
                confidence_score=0.0,
                error_message=f"Classification failed, defaulted to 'general': {str(e)}"
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Unexpected error: {str(e)}"
        
        logger.error(f"Unexpected error in process_url_endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        log_api_response("/process_url/", False, processing_time, error_msg)
        
        return URLProcessResponse(
            success=False,
            source_url=request.url,
            processing_time=processing_time,
            error_message=error_msg
        )


@api.post("/generate_overview/", response_model=GenerateOverviewResponse)
def generate_overview_endpoint(request: GenerateOverviewRequest) -> GenerateOverviewResponse:
    """
    Generate content-type-aware script overview from markdown content.
    
    This endpoint generates specialized overviews based on content type:
    - research: Uses existing research prompts and formatting
    - tutorial: Uses tutorial-focused prompts with code examples
    - general: Uses general content prompts focused on key points
    
    Requirements: 8.1, 8.3, 9.1, 9.2
    """
    start_time = time.time()
    
    # Log the incoming request (with truncated content for privacy)
    log_api_request("/generate_overview/", {
        "content_type": request.content_type,
        "method": request.method,
        "source_identifier": request.source_identifier,
        "content_length": len(request.content)
    })
    
    try:
        logger.info(f"Generating {request.content_type} overview using {request.method}")
        
        # Validate content length
        if len(request.content.strip()) < 10:
            error_msg = "Content is too short (minimum 10 characters required)"
            processing_time = time.time() - start_time
            log_api_response("/generate_overview/", False, processing_time, error_msg)
            
            return GenerateOverviewResponse(
                success=False,
                processing_time=processing_time,
                error_message=error_msg
            )
        
        # Generate overview using the appropriate generator
        script = generate_overview_by_type(
            content_type=request.content_type,
            markdown=request.content,
            source_identifier=request.source_identifier,
            method=request.method
        )
        
        processing_time = time.time() - start_time
        log_api_response("/generate_overview/", True, processing_time)
        
        return GenerateOverviewResponse(
            success=True,
            script=script,
            processing_time=processing_time
        )
        
    except ValueError as e:
        processing_time = time.time() - start_time
        error_msg = f"Validation error: {str(e)}"
        
        logger.error(f"Validation error in generate_overview_endpoint: {str(e)}")
        log_api_response("/generate_overview/", False, processing_time, error_msg)
        
        return GenerateOverviewResponse(
            success=False,
            processing_time=processing_time,
            error_message=error_msg
        )
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Script generation failed: {str(e)}"
        
        logger.error(f"Unexpected error in generate_overview_endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        log_api_response("/generate_overview/", False, processing_time, error_msg)
        
        return GenerateOverviewResponse(
            success=False,
            processing_time=processing_time,
            error_message=error_msg
        )


@cli.command("process_url")
def process_url_cli(url: str) -> None:
    """CLI command to process a URL and display results"""
    try:
        request = URLProcessRequest(url=url)
        result = process_url_endpoint(request)
        
        if result.success:
            print(f"✅ Successfully processed URL: {url}")
            print(f"📄 Content type: {result.content_type}")
            print(f"🔧 Source type: {result.source_type}")
            print(f"⏱️  Processing time: {result.processing_time:.2f}s")
            if result.paper_id:
                print(f"📋 Paper ID: {result.paper_id}")
            if result.confidence_score:
                print(f"🎯 Confidence: {result.confidence_score:.2f}")
        else:
            print(f"❌ Failed to process URL: {url}")
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"❌ CLI error: {str(e)}")


@cli.command("generate_overview")
def generate_overview_cli(
    content_file: str,
    content_type: Literal["research", "tutorial", "general"],
    source_identifier: str,
    method: Literal["openai", "gemini", "groq", "openrouter"] = "openrouter"
) -> None:
    """CLI command to generate overview from a markdown file"""
    try:
        # Read content from file
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        request = GenerateOverviewRequest(
            content=content,
            content_type=content_type,
            source_identifier=source_identifier,
            method=method
        )
        
        result = generate_overview_endpoint(request)
        
        if result.success:
            print(f"✅ Successfully generated {content_type} overview")
            print(f"⏱️  Processing time: {result.processing_time:.2f}s")
            print("\n📝 Generated Script:")
            print("=" * 50)
            print(result.script)
        else:
            print(f"❌ Failed to generate overview")
            print(f"Error: {result.error_message}")
            
    except FileNotFoundError:
        print(f"❌ File not found: {content_file}")
    except Exception as e:
        print(f"❌ CLI error: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    logging.info("info")
    cli()
