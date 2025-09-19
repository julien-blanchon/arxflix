"""
Tests for enhanced script generation with content type awareness.

This module tests the enhanced generate_script functionality that supports
different content types (research, tutorial, general) with specialized prompts.

Requirements: 5.1, 5.2, 6.1, 6.2, 7.1, 7.2
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from backend.utils.generate_script import process_script
from backend.utils.overview_generators import generate_overview_by_type


class TestEnhancedScriptGeneration(unittest.TestCase):
    """Test enhanced script generation with content type awareness."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_research_content = """
        # Deep Learning for Natural Language Processing
        
        ## Abstract
        This paper presents a novel approach to natural language processing using deep learning techniques.
        We propose a new architecture that achieves state-of-the-art results on multiple benchmarks.
        
        ## Introduction
        Natural language processing has seen significant advances with the introduction of transformer models.
        
        ## Methodology
        Our approach uses a multi-layer transformer architecture with attention mechanisms.
        
        ## Results
        We evaluated our model on GLUE benchmark and achieved 95% accuracy.
        
        ## Conclusion
        The proposed method demonstrates superior performance compared to existing approaches.
        """
        
        self.sample_tutorial_content = """
        # Building a REST API with FastAPI
        
        ## Introduction
        In this tutorial, we'll learn how to build a REST API using FastAPI, a modern Python web framework.
        
        ## Prerequisites
        - Python 3.7+
        - Basic understanding of HTTP
        
        ## Step 1: Installation
        First, install FastAPI and Uvicorn:
        ```bash
        pip install fastapi uvicorn
        ```
        
        ## Step 2: Create Your First API
        Create a file called `main.py`:
        ```python
        from fastapi import FastAPI
        
        app = FastAPI()
        
        @app.get("/")
        def read_root():
            return {"Hello": "World"}
        ```
        
        ## Step 3: Run the Server
        Run your API server:
        ```bash
        uvicorn main:app --reload
        ```
        
        ## Conclusion
        You've successfully created your first FastAPI application!
        """
        
        self.sample_general_content = """
        # The Future of Remote Work: Trends and Insights
        
        ## Introduction
        Remote work has transformed the modern workplace, accelerating during the COVID-19 pandemic.
        
        ## Key Trends
        
        ### Increased Adoption
        Companies worldwide have embraced remote work policies, with 42% of workers now working remotely.
        
        ### Technology Integration
        Video conferencing, collaboration tools, and cloud computing have become essential.
        
        ### Work-Life Balance
        Remote work offers flexibility but also presents challenges in maintaining boundaries.
        
        ## Benefits
        - Reduced commuting time
        - Access to global talent
        - Cost savings for companies
        
        ## Challenges
        - Communication barriers
        - Isolation and loneliness
        - Difficulty in team collaboration
        
        ## Future Outlook
        Hybrid work models are expected to become the norm, combining remote and office work.
        """

    @patch('backend.utils.generate_script._process_script_openrouter')
    def test_research_content_uses_existing_prompts(self, mock_process_script):
        """Test that research content continues using existing research prompts."""
        mock_process_script.return_value = "\\Headline: Research Overview\n\\Text: This is a research paper."
        
        # Test research content type
        result = process_script(
            method="openrouter",
            paper_markdown=self.sample_research_content,
            paper_id="2024.12345",
            end_point_base_url="",
            from_pdf=False,
            content_type="research"
        )
        
        # For research content, it should use the legacy processing
        mock_process_script.assert_called_once()
        
        # The result should be processed through the existing research pipeline
        self.assertIsInstance(result, str)
        self.assertEqual(result, "\\Headline: Research Overview\n\\Text: This is a research paper.")

    @patch('backend.utils.overview_generators.generate_overview_by_type')
    def test_tutorial_content_uses_tutorial_prompts(self, mock_generate_overview):
        """Test that tutorial content uses tutorial-focused prompts."""
        mock_generate_overview.return_value = "\\Headline: Tutorial Overview\n\\Text: This is a tutorial."
        
        # Test tutorial content type
        result = process_script(
            method="openrouter",
            paper_markdown=self.sample_tutorial_content,
            paper_id="tutorial_content",
            end_point_base_url="",
            from_pdf=False,
            content_type="tutorial"
        )
        
        # Should call the overview generator for tutorial content
        mock_generate_overview.assert_called_once_with(
            content_type="tutorial",
            markdown=self.sample_tutorial_content,
            source_identifier="tutorial_content",
            method="openrouter"
        )
        
        self.assertEqual(result, "\\Headline: Tutorial Overview\n\\Text: This is a tutorial.")

    @patch('backend.utils.overview_generators.generate_overview_by_type')
    def test_general_content_uses_general_prompts(self, mock_generate_overview):
        """Test that general content uses general overview prompts."""
        mock_generate_overview.return_value = "\\Headline: General Overview\n\\Text: This is general content."
        
        # Test general content type
        result = process_script(
            method="openrouter",
            paper_markdown=self.sample_general_content,
            paper_id="general_content",
            end_point_base_url="",
            from_pdf=False,
            content_type="general"
        )
        
        # Should call the overview generator for general content
        mock_generate_overview.assert_called_once_with(
            content_type="general",
            markdown=self.sample_general_content,
            source_identifier="general_content",
            method="openrouter"
        )
        
        self.assertEqual(result, "\\Headline: General Overview\n\\Text: This is general content.")

    @patch('backend.utils.generate_script._process_script_openrouter')
    def test_backward_compatibility_default_research(self, mock_process_script):
        """Test that default behavior maintains backward compatibility with research content."""
        mock_process_script.return_value = "\\Headline: Legacy Research\n\\Text: Legacy processing."
        
        # Test without specifying content_type (should default to research)
        result = process_script(
            method="openrouter",
            paper_markdown=self.sample_research_content,
            paper_id="2024.12345",
            end_point_base_url="",
            from_pdf=False
            # content_type not specified - should default to "research"
        )
        
        # Should use legacy processing for research content
        mock_process_script.assert_called_once()
        self.assertEqual(result, "\\Headline: Legacy Research\n\\Text: Legacy processing.")

    def test_method_mapping_for_overview_generators(self):
        """Test that method names are correctly mapped for overview generators."""
        with patch('backend.utils.overview_generators.generate_overview_by_type') as mock_generate:
            mock_generate.return_value = "test script"
            
            # Test different methods
            methods_to_test = ["openai", "gemini", "groq", "openrouter"]
            
            for method in methods_to_test:
                process_script(
                    method=method,
                    paper_markdown=self.sample_tutorial_content,
                    paper_id="test",
                    end_point_base_url="",
                    from_pdf=False,
                    content_type="tutorial"
                )
                
                # Verify the method was passed correctly
                mock_generate.assert_called_with(
                    content_type="tutorial",
                    markdown=self.sample_tutorial_content,
                    source_identifier="test",
                    method=method
                )

    @patch('backend.utils.overview_generators.generate_overview_by_type')
    def test_local_method_fallback_for_non_research(self, mock_generate):
        """Test that local method falls back to openrouter for non-research content."""
        mock_generate.return_value = "test script"
        
        with patch('backend.utils.generate_script.logger') as mock_logger:
            result = process_script(
                method="local",
                paper_markdown=self.sample_tutorial_content,
                paper_id="test",
                end_point_base_url="http://localhost:8000",
                from_pdf=False,
                content_type="tutorial"
            )
            
            # Should log a warning about fallback
            mock_logger.warning.assert_called_with(
                "Local method not supported for tutorial/general content, falling back to openrouter"
            )
            
            # Should call with openrouter method
            mock_generate.assert_called_with(
                content_type="tutorial",
                markdown=self.sample_tutorial_content,
                source_identifier="test",
                method="openrouter"
            )

    def test_invalid_method_raises_error(self):
        """Test that invalid methods raise appropriate errors."""
        with self.assertRaises(ValueError) as context:
            process_script(
                method="invalid_method",  # This will cause an error in the method mapping
                paper_markdown=self.sample_tutorial_content,
                paper_id="test",
                end_point_base_url="",
                from_pdf=False,
                content_type="tutorial"
            )
        self.assertIn("not supported for content type", str(context.exception))

    @patch('backend.utils.generate_script._process_script_openrouter')
    def test_research_content_with_pdf_processing(self, mock_process_script):
        """Test research content processing with from_pdf=True."""
        mock_process_script.return_value = "\\Headline: PDF Research\n\\Text: From PDF."
        
        result = process_script(
            method="openrouter",
            paper_markdown=self.sample_research_content,
            paper_id="original_id",
            end_point_base_url="",
            from_pdf=True,
            content_type="research"
        )
        
        # Should use legacy processing and set paper_id to "paper_id"
        mock_process_script.assert_called_once()
        # The paper_id should be changed to "paper_id" for PDF processing
        call_args = mock_process_script.call_args[0]
        self.assertIn("paper_id", call_args)  # paper_id should be set to "paper_id"

    def test_content_type_parameter_validation(self):
        """Test that content_type parameter accepts only valid values."""
        valid_content_types = ["research", "tutorial", "general"]
        
        for content_type in valid_content_types:
            # Should not raise an error for valid content types
            try:
                with patch('backend.utils.overview_generators.generate_overview_by_type') as mock_generate:
                    mock_generate.return_value = "test script"
                    
                    if content_type == "research":
                        # Research uses legacy processing
                        with patch('backend.utils.generate_script._process_script_openrouter') as mock_legacy:
                            mock_legacy.return_value = "legacy script"
                            process_script(
                                method="openrouter",
                                paper_markdown=self.sample_research_content,
                                paper_id="test",
                                end_point_base_url="",
                                from_pdf=False,
                                content_type=content_type
                            )
                    else:
                        process_script(
                            method="openrouter",
                            paper_markdown=self.sample_tutorial_content,
                            paper_id="test",
                            end_point_base_url="",
                            from_pdf=False,
                            content_type=content_type
                        )
            except Exception as e:
                self.fail(f"Valid content_type '{content_type}' should not raise an error: {e}")


if __name__ == "__main__":
    unittest.main()