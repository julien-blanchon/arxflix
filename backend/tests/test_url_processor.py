"""
Unit tests for URL processor module.

Tests cover URL validation, arXiv detection, paper ID extraction,
comprehensive input processing scenarios, and Firecrawl integration.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.url_processor import (
    validate_url,
    is_arxiv_url,
    extract_arxiv_paper_id,
    is_arxiv_paper_id,
    process_url_input,
    get_url_domain,
    URLProcessingResult,
    FirecrawlResult,
    FirecrawlError,
    _get_firecrawl_client,
    process_url_with_firecrawl,
    process_any_url,
    is_firecrawl_available
)


class TestURLValidation(unittest.TestCase):
    """Test URL validation functionality"""
    
    def test_valid_urls(self):
        """Test that valid URLs are correctly identified"""
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "https://example.com/path/to/resource?param=value",
            "https://example.com:8080/path",
            "https://arxiv.org/abs/2404.02905",
            "http://www.nature.com/articles/nature12373",
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(validate_url(url), f"URL should be valid: {url}")
    
    def test_invalid_urls(self):
        """Test that invalid URLs are correctly rejected"""
        invalid_urls = [
            "",
            None,
            "not-a-url",
            "ftp://example.com",  # Wrong scheme
            "https://",  # No domain
            "https://localhost",  # No dot in domain
            "example.com",  # No scheme
            "www.example.com",  # No scheme
            "https:///path",  # Empty domain
            123,  # Not a string
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(validate_url(url), f"URL should be invalid: {url}")
    
    def test_url_with_whitespace(self):
        """Test URL validation with leading/trailing whitespace"""
        self.assertTrue(validate_url("  https://example.com  "))
        self.assertTrue(validate_url("\thttps://example.com\n"))


class TestArxivDetection(unittest.TestCase):
    """Test arXiv URL detection functionality"""
    
    def test_arxiv_urls(self):
        """Test that arXiv URLs are correctly identified"""
        arxiv_urls = [
            "https://arxiv.org/abs/2404.02905",
            "http://arxiv.org/abs/2404.02905",
            "https://arxiv.org/pdf/2404.02905.pdf",
            "https://ARXIV.ORG/abs/2404.02905",  # Case insensitive
            "https://www.arxiv.org/abs/2404.02905",
            "https://arxiv.org/abs/1234.5678v1",
        ]
        
        for url in arxiv_urls:
            with self.subTest(url=url):
                self.assertTrue(is_arxiv_url(url), f"Should detect arXiv URL: {url}")
    
    def test_non_arxiv_urls(self):
        """Test that non-arXiv URLs are correctly identified"""
        non_arxiv_urls = [
            "https://www.nature.com/articles/nature12373",
            "https://example.com/arxiv-like-path",
            "https://notarxiv.org/abs/2404.02905",
            "https://arxiv-mirror.com/abs/2404.02905",
            "",
            None,
        ]
        
        for url in non_arxiv_urls:
            with self.subTest(url=url):
                self.assertFalse(is_arxiv_url(url), f"Should not detect arXiv URL: {url}")


class TestArxivPaperIdExtraction(unittest.TestCase):
    """Test arXiv paper ID extraction functionality"""
    
    def test_extract_paper_id_from_urls(self):
        """Test extracting paper IDs from various arXiv URL formats"""
        test_cases = [
            ("https://arxiv.org/abs/2404.02905", "2404.02905"),
            ("http://arxiv.org/abs/2404.02905", "2404.02905"),
            ("https://arxiv.org/pdf/2404.02905.pdf", "2404.02905"),
            ("https://arxiv.org/abs/2404.02905v1", "2404.02905v1"),
            ("https://arxiv.org/abs/1234.56789", "1234.56789"),
            ("https://arxiv.org/abs/math/0309285", "math/0309285"),  # Old format
            ("https://arxiv.org/pdf/math/0309285v1", "math/0309285v1"),  # Old format with version
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url, expected=expected_id):
                result = extract_arxiv_paper_id(url)
                self.assertEqual(result, expected_id, f"Failed to extract ID from: {url}")
    
    def test_extract_paper_id_failures(self):
        """Test cases where paper ID extraction should fail"""
        invalid_cases = [
            "https://example.com/abs/2404.02905",  # Not arXiv
            "https://arxiv.org/abs/invalid-id",  # Invalid ID format
            "https://arxiv.org/abs/",  # No ID
            "https://arxiv.org/",  # No path
            "",
            None,
        ]
        
        for url in invalid_cases:
            with self.subTest(url=url):
                result = extract_arxiv_paper_id(url)
                self.assertIsNone(result, f"Should not extract ID from: {url}")


class TestArxivPaperIdValidation(unittest.TestCase):
    """Test arXiv paper ID validation (for direct IDs, not URLs)"""
    
    def test_valid_paper_ids(self):
        """Test that valid arXiv paper IDs are correctly identified"""
        valid_ids = [
            "2404.02905",
            "1234.5678",
            "2404.02905v1",
            "1234.56789v10",
            "math/0309285",  # Old format
            "cs/0309285v1",  # Old format with version
            "hep-th/9901001",  # Old format with hyphen
        ]
        
        for paper_id in valid_ids:
            with self.subTest(paper_id=paper_id):
                self.assertTrue(is_arxiv_paper_id(paper_id), f"Should be valid paper ID: {paper_id}")
    
    def test_invalid_paper_ids(self):
        """Test that invalid paper IDs are correctly rejected"""
        invalid_ids = [
            "https://arxiv.org/abs/2404.02905",  # URL, not ID
            "invalid-id",
            "2404",  # Too short
            "2404.029",  # Wrong format
            "",
            None,
            123,  # Not a string
        ]
        
        for paper_id in invalid_ids:
            with self.subTest(paper_id=paper_id):
                self.assertFalse(is_arxiv_paper_id(paper_id), f"Should be invalid paper ID: {paper_id}")


class TestProcessUrlInput(unittest.TestCase):
    """Test comprehensive URL input processing"""
    
    def test_arxiv_paper_id_input(self):
        """Test processing direct arXiv paper IDs"""
        test_cases = [
            "2404.02905",
            "1234.5678v1",
            "math/0309285",
        ]
        
        for paper_id in test_cases:
            with self.subTest(paper_id=paper_id):
                result = process_url_input(paper_id)
                self.assertTrue(result.is_valid)
                self.assertTrue(result.is_arxiv)
                self.assertEqual(result.paper_id, paper_id)
                self.assertIsNone(result.error_message)
    
    def test_arxiv_url_input(self):
        """Test processing arXiv URLs"""
        test_cases = [
            ("https://arxiv.org/abs/2404.02905", "2404.02905"),
            ("https://arxiv.org/pdf/1234.5678v1.pdf", "1234.5678v1"),
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = process_url_input(url)
                self.assertTrue(result.is_valid)
                self.assertTrue(result.is_arxiv)
                self.assertEqual(result.paper_id, expected_id)
                self.assertIsNone(result.error_message)
    
    def test_non_arxiv_url_input(self):
        """Test processing non-arXiv URLs"""
        test_cases = [
            "https://www.nature.com/articles/nature12373",
            "https://example.com/article",
            "http://blog.example.com/post/123",
        ]
        
        for url in test_cases:
            with self.subTest(url=url):
                result = process_url_input(url)
                self.assertTrue(result.is_valid)
                self.assertFalse(result.is_arxiv)
                self.assertIsNone(result.paper_id)
                self.assertIsNone(result.error_message)
    
    def test_invalid_input(self):
        """Test processing invalid inputs"""
        test_cases = [
            "",
            None,
            "invalid-url",
            "not-a-url-or-id",
            123,
        ]
        
        for invalid_input in test_cases:
            with self.subTest(input=invalid_input):
                result = process_url_input(invalid_input)
                self.assertFalse(result.is_valid)
                self.assertIsNotNone(result.error_message)
    
    def test_arxiv_url_extraction_failure(self):
        """Test handling of arXiv URLs where ID extraction fails"""
        # This is a theoretical case - our current implementation should handle all valid arXiv URLs
        # But we test the error handling path
        result = process_url_input("https://arxiv.org/abs/")
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error_message)


class TestGetUrlDomain(unittest.TestCase):
    """Test URL domain extraction functionality"""
    
    def test_extract_domain(self):
        """Test extracting domains from valid URLs"""
        test_cases = [
            ("https://www.example.com", "www.example.com"),
            ("http://example.com", "example.com"),
            ("https://subdomain.example.com/path", "subdomain.example.com"),
            ("https://arxiv.org/abs/2404.02905", "arxiv.org"),
            ("https://Example.COM/path", "example.com"),  # Case normalization
        ]
        
        for url, expected_domain in test_cases:
            with self.subTest(url=url):
                result = get_url_domain(url)
                self.assertEqual(result, expected_domain)
    
    def test_extract_domain_failures(self):
        """Test domain extraction from invalid URLs"""
        invalid_urls = [
            "invalid-url",
            "",
            None,
            "ftp://example.com",  # Invalid scheme
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                result = get_url_domain(url)
                self.assertIsNone(result)


class TestURLProcessingResult(unittest.TestCase):
    """Test URLProcessingResult dataclass"""
    
    def test_result_creation(self):
        """Test creating URLProcessingResult instances"""
        # Valid arXiv result
        result = URLProcessingResult(
            is_valid=True,
            is_arxiv=True,
            paper_id="2404.02905"
        )
        self.assertTrue(result.is_valid)
        self.assertTrue(result.is_arxiv)
        self.assertEqual(result.paper_id, "2404.02905")
        self.assertIsNone(result.error_message)
        
        # Error result
        error_result = URLProcessingResult(
            is_valid=False,
            is_arxiv=False,
            error_message="Invalid input"
        )
        self.assertFalse(error_result.is_valid)
        self.assertFalse(error_result.is_arxiv)
        self.assertIsNone(error_result.paper_id)
        self.assertEqual(error_result.error_message, "Invalid input")


class TestFirecrawlIntegration(unittest.TestCase):
    """Test Firecrawl integration functionality"""
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_get_firecrawl_client_success(self, mock_firecrawl_app):
        """Test successful Firecrawl client creation"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        client = _get_firecrawl_client()
        
        mock_firecrawl_app.assert_called_once_with(api_key='test-api-key')
        self.assertEqual(client, mock_client)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.url_processor.FirecrawlApp')
    def test_get_firecrawl_client_missing_api_key(self, mock_firecrawl_app):
        """Test Firecrawl client creation with missing API key"""
        mock_firecrawl_app.return_value = MagicMock()
        
        with self.assertRaises(FirecrawlError) as context:
            _get_firecrawl_client()
        
        self.assertEqual(context.exception.error_type, "api_key_missing")
        self.assertIn("FIRECRAWL_API_KEY", context.exception.message)
    
    @patch('utils.url_processor.FirecrawlApp', None)
    def test_get_firecrawl_client_library_not_available(self):
        """Test Firecrawl client creation when library is not available"""
        with self.assertRaises(FirecrawlError) as context:
            _get_firecrawl_client()
        
        self.assertEqual(context.exception.error_type, "dependency_missing")
        self.assertIn("firecrawl-py", context.exception.message)
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_get_firecrawl_client_initialization_error(self, mock_firecrawl_app):
        """Test Firecrawl client creation with initialization error"""
        mock_firecrawl_app.side_effect = Exception("Connection failed")
        
        with self.assertRaises(FirecrawlError) as context:
            _get_firecrawl_client()
        
        self.assertEqual(context.exception.error_type, "client_initialization_failed")
        self.assertIn("Connection failed", context.exception.message)


class TestFirecrawlProcessing(unittest.TestCase):
    """Test Firecrawl URL processing functionality"""
    
    def test_process_url_with_firecrawl_invalid_url(self):
        """Test Firecrawl processing with invalid URL"""
        result = process_url_with_firecrawl("invalid-url")
        
        self.assertFalse(result.success)
        self.assertIn("Invalid URL format", result.error_message)
        self.assertIsNotNone(result.processing_time)
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_process_url_with_firecrawl_success(self, mock_firecrawl_app):
        """Test successful Firecrawl processing"""
        # Mock the Firecrawl client and response
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        mock_response = {
            "success": True,
            "markdown": "# Test Article\n\nThis is test content from the web page.",
            "metadata": {
                "title": "Test Article",
                "url": "https://example.com/article"
            }
        }
        mock_client.scrape_url.return_value = mock_response
        
        result = process_url_with_firecrawl("https://example.com/article")
        
        self.assertTrue(result.success)
        self.assertEqual(result.markdown_content, "# Test Article\n\nThis is test content from the web page.")
        self.assertEqual(result.metadata["title"], "Test Article")
        self.assertIsNotNone(result.processing_time)
        
        # Verify the scrape_url was called with correct parameters
        mock_client.scrape_url.assert_called_once()
        call_args = mock_client.scrape_url.call_args
        self.assertEqual(call_args[0][0], "https://example.com/article")
        self.assertIn("formats", call_args[0][1])
        self.assertEqual(call_args[0][1]["formats"], ["markdown"])
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_process_url_with_firecrawl_empty_content(self, mock_firecrawl_app):
        """Test Firecrawl processing with empty content response"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        mock_response = {
            "success": True,
            "markdown": "",  # Empty content
            "metadata": {}
        }
        mock_client.scrape_url.return_value = mock_response
        
        result = process_url_with_firecrawl("https://example.com/article")
        
        self.assertFalse(result.success)
        self.assertIn("empty or minimal content", result.error_message)
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_process_url_with_firecrawl_api_error(self, mock_firecrawl_app):
        """Test Firecrawl processing with API error"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        mock_response = {
            "success": False,
            "error": "Rate limit exceeded"
        }
        mock_client.scrape_url.return_value = mock_response
        
        result = process_url_with_firecrawl("https://example.com/article")
        
        self.assertFalse(result.success)
        self.assertIn("Rate limit exceeded", result.error_message)
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    @patch('utils.url_processor.time.sleep')  # Mock sleep to speed up tests
    def test_process_url_with_firecrawl_retry_logic(self, mock_sleep, mock_firecrawl_app):
        """Test Firecrawl processing retry logic"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        # First two calls fail, third succeeds
        mock_client.scrape_url.side_effect = [
            Exception("Network error"),
            Exception("Timeout error"),
            {
                "success": True,
                "markdown": "# Success after retries",
                "metadata": {}
            }
        ]
        
        result = process_url_with_firecrawl("https://example.com/article", max_retries=3)
        
        self.assertTrue(result.success)
        self.assertEqual(result.markdown_content, "# Success after retries")
        self.assertEqual(mock_client.scrape_url.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Sleep called for retries
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    @patch('utils.url_processor.time.sleep')
    def test_process_url_with_firecrawl_max_retries_exceeded(self, mock_sleep, mock_firecrawl_app):
        """Test Firecrawl processing when max retries are exceeded"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        # All calls fail
        mock_client.scrape_url.side_effect = Exception("Persistent network error")
        
        result = process_url_with_firecrawl("https://example.com/article", max_retries=2)
        
        self.assertFalse(result.success)
        self.assertIn("Failed to process URL after 2 attempts", result.error_message)
        self.assertIn("Persistent network error", result.error_message)
        self.assertEqual(mock_client.scrape_url.call_count, 2)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.url_processor.FirecrawlApp')
    def test_process_url_with_firecrawl_missing_api_key(self, mock_firecrawl_app):
        """Test Firecrawl processing with missing API key"""
        mock_firecrawl_app.return_value = MagicMock()
        
        result = process_url_with_firecrawl("https://example.com/article")
        
        self.assertFalse(result.success)
        self.assertIn("FIRECRAWL_API_KEY", result.error_message)


class TestProcessAnyUrl(unittest.TestCase):
    """Test the unified URL processing function"""
    
    def test_process_any_url_invalid_url(self):
        """Test process_any_url with invalid URL"""
        with self.assertRaises(ValueError) as context:
            process_any_url("invalid-url")
        
        self.assertIn("Invalid URL format", str(context.exception))
    
    def test_process_any_url_arxiv_url(self):
        """Test process_any_url with arXiv URL"""
        # This test verifies the routing logic - actual arXiv processing would be mocked
        content, source_type = process_any_url("https://arxiv.org/abs/2404.02905")
        
        self.assertEqual(source_type, "arxiv")
        self.assertIn("2404.02905", content)
    
    def test_process_any_url_arxiv_url_invalid_paper_id(self):
        """Test process_any_url with arXiv URL that has invalid paper ID"""
        with self.assertRaises(ValueError) as context:
            process_any_url("https://arxiv.org/abs/invalid-id")
        
        self.assertIn("Could not extract paper ID", str(context.exception))
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_process_any_url_firecrawl_success(self, mock_firecrawl_app):
        """Test process_any_url with successful Firecrawl processing"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        mock_response = {
            "success": True,
            "markdown": "# Test Content",
            "metadata": {}
        }
        mock_client.scrape_url.return_value = mock_response
        
        content, source_type = process_any_url("https://example.com/article")
        
        self.assertEqual(source_type, "firecrawl")
        self.assertEqual(content, "# Test Content")
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_process_any_url_firecrawl_failure(self, mock_firecrawl_app):
        """Test process_any_url with Firecrawl processing failure"""
        mock_client = MagicMock()
        mock_firecrawl_app.return_value = mock_client
        
        mock_response = {
            "success": False,
            "error": "Processing failed"
        }
        mock_client.scrape_url.return_value = mock_response
        
        with self.assertRaises(FirecrawlError) as context:
            process_any_url("https://example.com/article")
        
        self.assertEqual(context.exception.error_type, "processing_failed")


class TestFirecrawlAvailability(unittest.TestCase):
    """Test Firecrawl availability checking"""
    
    @patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test-api-key'})
    @patch('utils.url_processor.FirecrawlApp')
    def test_is_firecrawl_available_success(self, mock_firecrawl_app):
        """Test Firecrawl availability check when properly configured"""
        mock_firecrawl_app.return_value = MagicMock()
        
        self.assertTrue(is_firecrawl_available())
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_firecrawl_available_missing_api_key(self):
        """Test Firecrawl availability check with missing API key"""
        self.assertFalse(is_firecrawl_available())
    
    @patch('utils.url_processor.FirecrawlApp', None)
    def test_is_firecrawl_available_library_missing(self):
        """Test Firecrawl availability check when library is not installed"""
        self.assertFalse(is_firecrawl_available())


class TestFirecrawlResult(unittest.TestCase):
    """Test FirecrawlResult dataclass"""
    
    def test_firecrawl_result_success(self):
        """Test creating successful FirecrawlResult"""
        result = FirecrawlResult(
            success=True,
            markdown_content="# Test Content",
            metadata={"title": "Test"},
            processing_time=1.5
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.markdown_content, "# Test Content")
        self.assertEqual(result.metadata["title"], "Test")
        self.assertEqual(result.processing_time, 1.5)
        self.assertIsNone(result.error_message)
    
    def test_firecrawl_result_failure(self):
        """Test creating failed FirecrawlResult"""
        result = FirecrawlResult(
            success=False,
            error_message="Processing failed",
            processing_time=0.5
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Processing failed")
        self.assertEqual(result.processing_time, 0.5)
        self.assertIsNone(result.markdown_content)
        self.assertIsNone(result.metadata)


class TestFirecrawlError(unittest.TestCase):
    """Test FirecrawlError exception class"""
    
    def test_firecrawl_error_basic(self):
        """Test basic FirecrawlError creation"""
        error = FirecrawlError("Test error message")
        
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.error_type, "unknown")
        self.assertEqual(error.details, {})
        self.assertEqual(str(error), "Test error message")
    
    def test_firecrawl_error_with_details(self):
        """Test FirecrawlError with error type and details"""
        details = {"api_key": "missing", "endpoint": "/scrape"}
        error = FirecrawlError(
            "API key missing",
            error_type="api_key_missing",
            details=details
        )
        
        self.assertEqual(error.message, "API key missing")
        self.assertEqual(error.error_type, "api_key_missing")
        self.assertEqual(error.details, details)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)