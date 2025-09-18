"""
URL Processing Module

This module provides utilities for URL validation, arXiv detection, paper ID extraction,
and Firecrawl integration for non-arXiv content processing.
It serves as the core infrastructure for processing various URL types in the ArxFlix system.
"""

import re
import urllib.parse
import os
import time
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

try:
    from firecrawl import FirecrawlApp
except ImportError:
    FirecrawlApp = None


@dataclass
class URLProcessingResult:
    """Result of URL processing operation"""
    is_valid: bool
    is_arxiv: bool
    paper_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class FirecrawlResult:
    """Result of Firecrawl processing operation"""
    success: bool
    markdown_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class FirecrawlError(Exception):
    """Custom exception for Firecrawl-related errors"""
    def __init__(self, message: str, error_type: str = "unknown", details: Dict[str, Any] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)


def validate_url(url: str) -> bool:
    """
    Validate if the provided string is a valid HTTP/HTTPS URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
        
    Requirements: 1.1, 1.2
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Check if URL has a valid scheme
    if not url.startswith(('http://', 'https://')):
        return False
    
    try:
        parsed = urllib.parse.urlparse(url)
        # Check if URL has all required components
        return all([
            parsed.scheme in ('http', 'https'),
            parsed.netloc,  # Must have a domain
            '.' in parsed.netloc  # Domain must have at least one dot
        ])
    except Exception:
        return False


def is_arxiv_url(url: str) -> bool:
    """
    Detect if a URL is an arXiv paper URL.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if URL is an arXiv URL, False otherwise
        
    Requirements: 2.1, 2.2
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip().lower()
    
    # Check for arxiv.org domain (must be the actual domain, not just contained in URL)
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain == 'arxiv.org'
    except Exception:
        return False


def extract_arxiv_paper_id(url: str) -> Optional[str]:
    """
    Extract arXiv paper ID from an arXiv URL.
    
    Supports various arXiv URL formats:
    - https://arxiv.org/abs/2404.02905
    - https://arxiv.org/pdf/2404.02905.pdf
    - http://arxiv.org/abs/2404.02905v1
    
    Args:
        url: The arXiv URL to extract paper ID from
        
    Returns:
        Optional[str]: The paper ID if found, None otherwise
        
    Requirements: 2.1, 2.3
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Pattern to match arXiv paper IDs (YYMM.NNNNN format, with optional version)
    # Supports both old format (subject-class/YYMMnnn) and new format (YYMM.NNNNN)
    arxiv_patterns = [
        # New format: YYMM.NNNNN with optional version
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)',
        # Handle PDF extension
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:\.pdf)?(?:v\d+)?',
        # Old format: subject-class/YYMMnnn
        r'arxiv\.org/(?:abs|pdf)/([a-z-]+/\d{7}(?:v\d+)?)',
    ]
    
    for pattern in arxiv_patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            paper_id = match.group(1)
            # Remove .pdf extension if present
            paper_id = re.sub(r'\.pdf$', '', paper_id, flags=re.IGNORECASE)
            return paper_id
    
    return None


def is_arxiv_paper_id(input_str: str) -> bool:
    """
    Check if a string is a valid arXiv paper ID (not a URL).
    
    Args:
        input_str: The string to check
        
    Returns:
        bool: True if it's a valid arXiv paper ID, False otherwise
        
    Requirements: 2.1, 2.2
    """
    if not input_str or not isinstance(input_str, str):
        return False
    
    input_str = input_str.strip()
    
    # Check for arXiv paper ID patterns
    patterns = [
        # New format: YYMM.NNNNN with optional version
        r'^\d{4}\.\d{4,5}(?:v\d+)?$',
        # Old format: subject-class/YYMMnnn
        r'^[a-z-]+/\d{7}(?:v\d+)?$',
    ]
    
    return any(re.match(pattern, input_str, re.IGNORECASE) for pattern in patterns)


def process_url_input(input_str: str) -> URLProcessingResult:
    """
    Process user input to determine if it's a valid URL or arXiv paper ID.
    
    Args:
        input_str: User input (URL or arXiv paper ID)
        
    Returns:
        URLProcessingResult: Processing result with validation and classification info
        
    Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
    """
    if not input_str or not isinstance(input_str, str):
        return URLProcessingResult(
            is_valid=False,
            is_arxiv=False,
            error_message="Input is empty or invalid"
        )
    
    input_str = input_str.strip()
    
    # Check if input is an arXiv paper ID (not a URL)
    if is_arxiv_paper_id(input_str):
        return URLProcessingResult(
            is_valid=True,
            is_arxiv=True,
            paper_id=input_str
        )
    
    # Check if input is a valid URL
    if not validate_url(input_str):
        return URLProcessingResult(
            is_valid=False,
            is_arxiv=False,
            error_message="Invalid URL format"
        )
    
    # Check if it's an arXiv URL
    if is_arxiv_url(input_str):
        paper_id = extract_arxiv_paper_id(input_str)
        if paper_id:
            return URLProcessingResult(
                is_valid=True,
                is_arxiv=True,
                paper_id=paper_id
            )
        else:
            return URLProcessingResult(
                is_valid=False,
                is_arxiv=True,
                error_message="Could not extract paper ID from arXiv URL"
            )
    
    # Valid non-arXiv URL
    return URLProcessingResult(
        is_valid=True,
        is_arxiv=False
    )


def get_url_domain(url: str) -> Optional[str]:
    """
    Extract domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Optional[str]: The domain if URL is valid, None otherwise
    """
    if not validate_url(url):
        return None
    
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def _get_firecrawl_client() -> FirecrawlApp:
    """
    Get configured Firecrawl client instance.
    
    Returns:
        FirecrawlApp: Configured Firecrawl client
        
    Raises:
        FirecrawlError: If Firecrawl is not available or API key is missing
        
    Requirements: 3.2
    """
    if FirecrawlApp is None:
        raise FirecrawlError(
            "Firecrawl library not available. Please install firecrawl-py.",
            error_type="dependency_missing"
        )
    
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise FirecrawlError(
            "FIRECRAWL_API_KEY environment variable is required for non-arXiv URL processing.",
            error_type="api_key_missing",
            details={"env_var": "FIRECRAWL_API_KEY"}
        )
    
    try:
        return FirecrawlApp(api_key=api_key)
    except Exception as e:
        raise FirecrawlError(
            f"Failed to initialize Firecrawl client: {str(e)}",
            error_type="client_initialization_failed",
            details={"original_error": str(e)}
        )


def process_url_with_firecrawl(url: str, max_retries: int = 3, timeout: int = 30) -> FirecrawlResult:
    """
    Process a URL using Firecrawl to extract markdown content.
    
    Args:
        url: The URL to process
        max_retries: Maximum number of retry attempts for failed requests
        timeout: Timeout in seconds for the request
        
    Returns:
        FirecrawlResult: Result containing markdown content or error information
        
    Requirements: 3.1, 3.3, 8.2
    """
    start_time = time.time()
    
    # Validate URL first
    if not validate_url(url):
        return FirecrawlResult(
            success=False,
            error_message="Invalid URL format",
            processing_time=time.time() - start_time
        )
    
    try:
        client = _get_firecrawl_client()
    except FirecrawlError as e:
        return FirecrawlResult(
            success=False,
            error_message=e.message,
            processing_time=time.time() - start_time
        )
    
    # Configure scraping options
    scrape_options = {
        "formats": ["markdown"],
        "timeout": timeout * 1000,  # Firecrawl expects milliseconds
        "waitFor": 2000  # Wait 2 seconds for dynamic content
    }
    
    last_error = None
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Add delay for retries (exponential backoff)
            if attempt > 0:
                delay = min(2 ** attempt, 10)  # Cap at 10 seconds
                time.sleep(delay)
            
            # Perform the scrape
            result = client.scrape_url(url, scrape_options)
            
            if result and isinstance(result, dict):
                # Check if we have an error
                if "error" in result:
                    return FirecrawlResult(
                        success=False,
                        error_message=f"Firecrawl error: {result['error']}",
                        processing_time=time.time() - start_time
                    )
                
                # Extract markdown content
                markdown_content = result.get("markdown", "")
                metadata = result.get("metadata", {})
                
                # Validate that we got meaningful content
                if not markdown_content or len(markdown_content.strip()) < 10:
                    return FirecrawlResult(
                        success=False,
                        error_message="Firecrawl returned empty or minimal content",
                        processing_time=time.time() - start_time
                    )
                
                return FirecrawlResult(
                    success=True,
                    markdown_content=markdown_content,
                    metadata=metadata,
                    processing_time=time.time() - start_time
                )
            else:
                return FirecrawlResult(
                    success=False,
                    error_message="No response from Firecrawl or invalid response format",
                    processing_time=time.time() - start_time
                )
                
        except FirecrawlError:
            raise  # Re-raise FirecrawlError as-is
        except Exception as e:
            last_error = e
            # For non-FirecrawlError exceptions, continue retrying
            continue
    
    # If we've exhausted all retries
    error_message = f"Failed to process URL after {max_retries} attempts"
    if last_error:
        error_message += f": {str(last_error)}"
    
    return FirecrawlResult(
        success=False,
        error_message=error_message,
        processing_time=time.time() - start_time
    )


def process_any_url(url: str) -> Tuple[str, str]:
    """
    Process any URL, automatically routing to arXiv processing or Firecrawl based on URL type.
    
    Args:
        url: The URL to process
        
    Returns:
        Tuple[str, str]: (markdown_content, source_type) where source_type is "arxiv" or "firecrawl"
        
    Raises:
        FirecrawlError: If processing fails
        ValueError: If URL is invalid
        
    Requirements: 2.4, 3.1, 3.3
    """
    # First validate the URL
    if not validate_url(url):
        raise ValueError(f"Invalid URL format: {url}")
    
    # Check if it's an arXiv URL
    if is_arxiv_url(url):
        paper_id = extract_arxiv_paper_id(url)
        if not paper_id:
            raise ValueError(f"Could not extract paper ID from arXiv URL: {url}")
        
        # For arXiv URLs, we would use the existing arXiv processing
        # This is a placeholder - the actual arXiv processing would be implemented
        # in the generate_paper.py module
        return f"arXiv paper content for {paper_id}", "arxiv"
    
    # For non-arXiv URLs, use Firecrawl
    result = process_url_with_firecrawl(url)
    
    if not result.success:
        raise FirecrawlError(
            result.error_message or "Failed to process URL with Firecrawl",
            error_type="processing_failed"
        )
    
    return result.markdown_content, "firecrawl"


def is_firecrawl_available() -> bool:
    """
    Check if Firecrawl is available and properly configured.
    
    Returns:
        bool: True if Firecrawl is available and configured, False otherwise
        
    Requirements: 3.2, 8.2
    """
    try:
        _get_firecrawl_client()
        return True
    except FirecrawlError:
        return False