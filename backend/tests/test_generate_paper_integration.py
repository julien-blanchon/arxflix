"""
Integration tests for the enhanced generate_paper function.

These tests verify that the generate_paper function correctly handles:
1. Traditional arXiv paper ID input (backward compatibility)
2. arXiv URL input with proper routing
3. Non-arXiv URL input with Firecrawl processing
4. Error handling for various failure scenarios
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from backend.main import generate_paper
from backend.utils.url_processor import FirecrawlResult, FirecrawlError


class TestGeneratePaperIntegration(unittest.TestCase):
    """Integration tests for enhanced generate_paper function"""

    def test_generate_paper_with_arxiv_paper_id_backward_compatibility(self):
        """Test that traditional arXiv paper ID input still works (backward compatibility)"""
        # Mock the process_article function
        with patch('backend.main.process_article') as mock_process_article:
            mock_process_article.return_value = "# Test Paper\n\nThis is a test paper."
            
            # Test with traditional paper_id parameter
            result = generate_paper(method="arxiv_html", paper_id="2404.02905")
            
            # Verify the result
            assert result == "# Test Paper\n\nThis is a test paper."
            
            # Verify process_article was called with correct parameters
            mock_process_article.assert_called_once_with("arxiv_html", "2404.02905", None)

    def test_generate_paper_with_arxiv_paper_id_and_pdf_path(self):
        """Test backward compatibility with PDF processing"""
        with patch('backend.main.process_article') as mock_process_article:
            mock_process_article.return_value = "# PDF Paper\n\nThis is from PDF."
            
            result = generate_paper(method="pdf", paper_id="2404.02905", pdf_path="/path/to/paper.pdf")
            
            assert result == "# PDF Paper\n\nThis is from PDF."
            mock_process_article.assert_called_once_with("pdf", "2404.02905", "/path/to/paper.pdf")

    def test_generate_paper_with_arxiv_url_routes_to_arxiv_processing(self):
        """Test that arXiv URLs are properly detected and routed to arXiv processing"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.extract_arxiv_paper_id') as mock_extract_paper_id, \
             patch('backend.main.process_article') as mock_process_article:
            
            # Setup mocks
            mock_is_arxiv_url.return_value = True
            mock_extract_paper_id.return_value = "2404.02905"
            mock_process_article.return_value = "# ArXiv Paper\n\nThis is from arXiv URL."
            
            # Test with arXiv URL
            result = generate_paper(
                method="arxiv_html", 
                url="https://arxiv.org/abs/2404.02905"
            )
            
            # Verify the result
            assert result == "# ArXiv Paper\n\nThis is from arXiv URL."
            
            # Verify the correct functions were called
            mock_is_arxiv_url.assert_called_once_with("https://arxiv.org/abs/2404.02905")
            mock_extract_paper_id.assert_called_once_with("https://arxiv.org/abs/2404.02905")
            mock_process_article.assert_called_once_with("arxiv_html", "2404.02905", None)

    def test_generate_paper_with_arxiv_url_different_formats(self):
        """Test that different arXiv URL formats are handled correctly"""
        test_cases = [
            ("https://arxiv.org/abs/2404.02905", "2404.02905"),
            ("https://arxiv.org/pdf/2404.02905.pdf", "2404.02905"),
            ("http://arxiv.org/abs/2404.02905v1", "2404.02905v1"),
        ]
        
        for url, expected_paper_id in test_cases:
            with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
                 patch('backend.main.extract_arxiv_paper_id') as mock_extract_paper_id, \
                 patch('backend.main.process_article') as mock_process_article:
                
                mock_is_arxiv_url.return_value = True
                mock_extract_paper_id.return_value = expected_paper_id
                mock_process_article.return_value = f"# Paper {expected_paper_id}"
                
                result = generate_paper(method="arxiv_html", url=url)
                
                assert result == f"# Paper {expected_paper_id}"
                mock_extract_paper_id.assert_called_once_with(url)
                mock_process_article.assert_called_once_with("arxiv_html", expected_paper_id, None)

    def test_generate_paper_with_non_arxiv_url_uses_firecrawl(self):
        """Test that non-arXiv URLs are processed using Firecrawl"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.process_url_with_firecrawl') as mock_firecrawl:
            
            # Setup mocks
            mock_is_arxiv_url.return_value = False
            mock_firecrawl.return_value = FirecrawlResult(
                success=True,
                markdown_content="# Web Article\n\nThis is from a web page.",
                processing_time=2.5
            )
            
            # Test with non-arXiv URL
            result = generate_paper(
                method="arxiv_html",  # method is ignored for non-arXiv URLs
                url="https://example.com/article"
            )
            
            # Verify the result
            assert result == "# Web Article\n\nThis is from a web page."
            
            # Verify the correct functions were called
            mock_is_arxiv_url.assert_called_once_with("https://example.com/article")
            mock_firecrawl.assert_called_once_with("https://example.com/article")

    def test_generate_paper_arxiv_url_extraction_failure(self):
        """Test error handling when arXiv paper ID extraction fails"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.extract_arxiv_paper_id') as mock_extract_paper_id:
            
            mock_is_arxiv_url.return_value = True
            mock_extract_paper_id.return_value = None  # Extraction failed
            
            # Should raise HTTPException
            with self.assertRaises(HTTPException) as exc_info:
                generate_paper(method="arxiv_html", url="https://arxiv.org/abs/invalid")
            
            self.assertEqual(exc_info.exception.status_code, 400)
            self.assertIn("Could not extract paper ID from arXiv URL", str(exc_info.exception.detail))

    def test_generate_paper_firecrawl_failure(self):
        """Test error handling when Firecrawl processing fails"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.process_url_with_firecrawl') as mock_firecrawl:
            
            mock_is_arxiv_url.return_value = False
            mock_firecrawl.return_value = FirecrawlResult(
                success=False,
                error_message="Failed to scrape URL: Connection timeout",
                processing_time=30.0
            )
            
            # Should raise HTTPException
            with self.assertRaises(HTTPException) as exc_info:
                generate_paper(method="arxiv_html", url="https://example.com/timeout")
            
            self.assertEqual(exc_info.exception.status_code, 400)
            self.assertIn("Failed to process URL", str(exc_info.exception.detail))

    def test_generate_paper_no_parameters_provided(self):
        """Test error handling when neither paper_id nor url is provided"""
        with self.assertRaises(HTTPException) as exc_info:
            generate_paper(method="arxiv_html")
        
        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("Either 'paper_id' or 'url' parameter must be provided", str(exc_info.exception.detail))

    def test_generate_paper_both_paper_id_and_url_provided(self):
        """Test that URL takes precedence when both paper_id and url are provided"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.extract_arxiv_paper_id') as mock_extract_paper_id, \
             patch('backend.main.process_article') as mock_process_article:
            
            mock_is_arxiv_url.return_value = True
            mock_extract_paper_id.return_value = "2404.02905"
            mock_process_article.return_value = "# URL Paper"
            
            # Provide both parameters - URL should take precedence
            result = generate_paper(
                method="arxiv_html",
                paper_id="1234.5678",  # This should be ignored
                url="https://arxiv.org/abs/2404.02905"
            )
            
            assert result == "# URL Paper"
            # Should extract from URL, not use the paper_id parameter
            mock_extract_paper_id.assert_called_once_with("https://arxiv.org/abs/2404.02905")
            mock_process_article.assert_called_once_with("arxiv_html", "2404.02905", None)

    def test_generate_paper_process_article_exception(self):
        """Test error handling when process_article raises an exception"""
        with patch('backend.main.process_article') as mock_process_article:
            mock_process_article.side_effect = ValueError("Invalid paper ID format")
            
            with self.assertRaises(HTTPException) as exc_info:
                generate_paper(method="arxiv_html", paper_id="invalid-id")
            
            self.assertEqual(exc_info.exception.status_code, 400)
            self.assertIn("Invalid paper ID format", str(exc_info.exception.detail))

    def test_generate_paper_firecrawl_exception(self):
        """Test error handling when Firecrawl raises an exception"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.process_url_with_firecrawl') as mock_firecrawl:
            
            mock_is_arxiv_url.return_value = False
            mock_firecrawl.side_effect = FirecrawlError("API key not found", "api_key_missing")
            
            with self.assertRaises(HTTPException) as exc_info:
                generate_paper(method="arxiv_html", url="https://example.com/article")
            
            self.assertEqual(exc_info.exception.status_code, 400)
            self.assertIn("API key not found", str(exc_info.exception.detail))

    def test_generate_paper_maintains_method_parameter_for_arxiv(self):
        """Test that the method parameter is correctly passed through for arXiv processing"""
        methods_to_test = ["arxiv_gpt", "arxiv_html", "pdf"]
        
        for method in methods_to_test:
            with patch('backend.main.process_article') as mock_process_article:
                mock_process_article.return_value = f"# Paper via {method}"
                
                result = generate_paper(method=method, paper_id="2404.02905")
                
                assert result == f"# Paper via {method}"
                mock_process_article.assert_called_once_with(method, "2404.02905", None)

    def test_generate_paper_logging_behavior(self):
        """Test that appropriate logging occurs during processing"""
        with patch('backend.main.process_article') as mock_process_article, \
             patch('backend.main.logger') as mock_logger:
            
            mock_process_article.return_value = "# Test Paper"
            
            # Test paper_id logging
            generate_paper(method="arxiv_html", paper_id="2404.02905")
            
            mock_logger.info.assert_called_with(
                "Generating paper markdown using method: arxiv_html and paper_id: 2404.02905"
            )

    def test_generate_paper_url_logging_behavior(self):
        """Test logging behavior for URL processing"""
        with patch('backend.main.is_arxiv_url') as mock_is_arxiv_url, \
             patch('backend.main.extract_arxiv_paper_id') as mock_extract_paper_id, \
             patch('backend.main.process_article') as mock_process_article, \
             patch('backend.main.logger') as mock_logger:
            
            mock_is_arxiv_url.return_value = True
            mock_extract_paper_id.return_value = "2404.02905"
            mock_process_article.return_value = "# Test Paper"
            
            generate_paper(method="arxiv_html", url="https://arxiv.org/abs/2404.02905")
            
            # Check that URL processing was logged
            mock_logger.info.assert_any_call("Processing URL: https://arxiv.org/abs/2404.02905")
            mock_logger.info.assert_any_call("Detected arXiv URL, extracting paper ID: 2404.02905")

    def test_generate_paper_error_logging(self):
        """Test that errors are properly logged"""
        with patch('backend.main.process_article') as mock_process_article, \
             patch('backend.main.logger') as mock_logger:
            
            mock_process_article.side_effect = ValueError("Test error")
            
            with self.assertRaises(HTTPException):
                generate_paper(method="arxiv_html", paper_id="2404.02905")
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            logged_message = mock_logger.error.call_args[0][0]
            assert "Error in generate_paper: Test error" in logged_message


class TestGeneratePaperRequirements(unittest.TestCase):
    """Tests specifically for the requirements mentioned in the task"""

    def test_requirement_2_4_url_processing_logic_routes_correctly(self):
        """Requirement 2.4: Add URL processing logic that routes to appropriate processor"""
        # Test arXiv URL routing
        with patch('backend.main.is_arxiv_url', return_value=True), \
             patch('backend.main.extract_arxiv_paper_id', return_value="2404.02905"), \
             patch('backend.main.process_article', return_value="arXiv content") as mock_process:
            
            result = generate_paper(method="arxiv_html", url="https://arxiv.org/abs/2404.02905")
            assert result == "arXiv content"
            mock_process.assert_called_once()

        # Test non-arXiv URL routing
        with patch('backend.main.is_arxiv_url', return_value=False), \
             patch('backend.main.process_url_with_firecrawl') as mock_firecrawl:
            
            mock_firecrawl.return_value = FirecrawlResult(
                success=True, 
                markdown_content="Firecrawl content"
            )
            
            result = generate_paper(method="arxiv_html", url="https://example.com")
            assert result == "Firecrawl content"
            mock_firecrawl.assert_called_once()

    def test_requirement_5_3_research_content_compatibility(self):
        """Requirement 5.3: Research content maintains compatibility with current features"""
        with patch('backend.main.process_article') as mock_process_article:
            mock_process_article.return_value = "# Research Paper\n\n## Abstract\n\nThis is research."
            
            # Test that research content (arXiv) uses existing logic
            result = generate_paper(method="arxiv_html", paper_id="2404.02905")
            
            assert "Research Paper" in result
            assert "Abstract" in result
            mock_process_article.assert_called_once_with("arxiv_html", "2404.02905", None)

    def test_requirement_5_4_research_content_from_other_sources(self):
        """Requirement 5.4: Research content from other sources adapts format"""
        with patch('backend.main.is_arxiv_url', return_value=False), \
             patch('backend.main.process_url_with_firecrawl') as mock_firecrawl:
            
            # Simulate research content from non-arXiv source
            mock_firecrawl.return_value = FirecrawlResult(
                success=True,
                markdown_content="# Research from Journal\n\n## Methodology\n\nThis is research from another source."
            )
            
            result = generate_paper(method="arxiv_html", url="https://journal.example.com/paper")
            
            assert "Research from Journal" in result
            assert "Methodology" in result
            mock_firecrawl.assert_called_once()

    def test_requirement_9_3_backward_compatibility_maintained(self):
        """Requirement 9.3: Backward compatibility with current arXiv-only functionality"""
        with patch('backend.main.process_article') as mock_process_article:
            mock_process_article.return_value = "# Legacy ArXiv Paper"
            
            # Test that existing arXiv-only calls work exactly as before
            result = generate_paper(method="arxiv_gpt", paper_id="2404.02905")
            
            assert result == "# Legacy ArXiv Paper"
            mock_process_article.assert_called_once_with("arxiv_gpt", "2404.02905", None)
            
            # Test with PDF method
            result = generate_paper(method="pdf", paper_id="2404.02905", pdf_path="/path/to/pdf")
            mock_process_article.assert_called_with("pdf", "2404.02905", "/path/to/pdf")

    def test_requirement_9_4_same_data_flow_patterns(self):
        """Requirement 9.4: New processing methods follow same data flow patterns"""
        # Test that both old and new methods return the same type of data (markdown string)
        
        # Old method (paper_id)
        with patch('backend.main.process_article', return_value="# ArXiv Paper Content"):
            old_result = generate_paper(method="arxiv_html", paper_id="2404.02905")
            assert isinstance(old_result, str)
            assert old_result.startswith("#")
        
        # New method (arXiv URL)
        with patch('backend.main.is_arxiv_url', return_value=True), \
             patch('backend.main.extract_arxiv_paper_id', return_value="2404.02905"), \
             patch('backend.main.process_article', return_value="# ArXiv URL Paper Content"):
            
            new_arxiv_result = generate_paper(method="arxiv_html", url="https://arxiv.org/abs/2404.02905")
            assert isinstance(new_arxiv_result, str)
            assert new_arxiv_result.startswith("#")
        
        # New method (Firecrawl URL)
        with patch('backend.main.is_arxiv_url', return_value=False), \
             patch('backend.main.process_url_with_firecrawl') as mock_firecrawl:
            
            mock_firecrawl.return_value = FirecrawlResult(
                success=True,
                markdown_content="# Firecrawl Paper Content"
            )
            
            new_firecrawl_result = generate_paper(method="arxiv_html", url="https://example.com/paper")
            assert isinstance(new_firecrawl_result, str)
            assert new_firecrawl_result.startswith("#")