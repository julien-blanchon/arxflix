"""
Unit tests for overview generators.

Tests the specialized overview generation for research, tutorial, and general content types.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from backend.utils.overview_generators import (
    generate_research_overview,
    generate_tutorial_overview,
    generate_general_overview,
    generate_overview_by_type,
    _generate_overview_openai,
    _generate_overview_openrouter,
    _generate_overview_gemini,
    _generate_overview_groq,
    RESEARCH_OVERVIEW_PROMPT,
    TUTORIAL_OVERVIEW_PROMPT,
    GENERAL_OVERVIEW_PROMPT
)


class TestOverviewGenerators(unittest.TestCase):
    """Test suite for overview generators."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_research_content = """
        # Deep Learning for Computer Vision: A Comprehensive Survey

        ## Abstract
        This paper presents a comprehensive survey of deep learning techniques for computer vision tasks.
        We analyze various architectures including CNNs, Vision Transformers, and their applications.

        ## Introduction
        Computer vision has been revolutionized by deep learning approaches...

        ## Methodology
        We conducted experiments using ResNet-50 and Vision Transformer architectures...

        ## Results
        Our experiments show that Vision Transformers achieve 95.2% accuracy on ImageNet...

        ## Conclusion
        Deep learning continues to advance the state-of-the-art in computer vision...
        """

        self.sample_tutorial_content = """
        # How to Build a REST API with FastAPI

        ## Introduction
        In this tutorial, you'll learn how to build a REST API using FastAPI, a modern Python web framework.

        ## Prerequisites
        - Python 3.7+
        - Basic knowledge of Python
        - Understanding of HTTP methods

        ## Step 1: Installation
        First, install FastAPI and Uvicorn:
        ```bash
        pip install fastapi uvicorn
        ```

        ## Step 2: Create Your First Endpoint
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
        # The Future of Remote Work: Trends and Predictions

        ## Introduction
        Remote work has become increasingly popular, especially after the global pandemic.
        This article explores current trends and future predictions for remote work.

        ## Current State
        According to recent surveys, 42% of the workforce now works remotely at least part-time.
        Companies are adapting their policies to accommodate flexible work arrangements.

        ## Key Benefits
        - Increased productivity
        - Better work-life balance
        - Reduced commuting costs
        - Access to global talent

        ## Challenges
        - Communication barriers
        - Maintaining company culture
        - Technology requirements
        - Time zone coordination

        ## Future Predictions
        Experts predict that hybrid work models will become the norm by 2025.
        Virtual reality meetings and AI-powered collaboration tools will enhance remote work experiences.

        ## Conclusion
        Remote work is here to stay, and organizations must adapt to thrive in this new landscape.
        """

        self.mock_script_response = {
            "title": "Test Video Title",
            "target_duration_minutes": 5.5,
            "components": [
                {
                    "component_type": "Headline",
                    "content": "Test Headline",
                    "position": 0
                },
                {
                    "component_type": "Text",
                    "content": "Test content for the video script.",
                    "position": 1
                },
                {
                    "component_type": "Code_Snippet",
                    "content": "def example_function():\n    return 'Hello World'",
                    "position": 2
                }
            ]
        }
        
        # Separate mock response for research content (which still has paper_id)
        self.mock_research_script_response = {
            "title": "Test Research Video Title",
            "paper_id": "test_id",
            "target_duration_minutes": 5.5,
            "components": [
                {
                    "component_type": "Headline",
                    "content": "Test Research Headline",
                    "position": 0
                },
                {
                    "component_type": "Text",
                    "content": "Test research content for the video script.",
                    "position": 1
                }
            ]
        }

    def test_research_overview_prompt_content(self):
        """Test that research overview prompt contains research-specific instructions."""
        self.assertIn("research-focused audience", RESEARCH_OVERVIEW_PROMPT)
        self.assertIn("methodology, findings, implications", RESEARCH_OVERVIEW_PROMPT)
        self.assertIn("academic rigor", RESEARCH_OVERVIEW_PROMPT)
        self.assertIn("technical details", RESEARCH_OVERVIEW_PROMPT)

    def test_tutorial_overview_prompt_content(self):
        """Test that tutorial overview prompt contains tutorial-specific instructions."""
        self.assertIn("educational content", TUTORIAL_OVERVIEW_PROMPT)
        self.assertIn("learning objectives", TUTORIAL_OVERVIEW_PROMPT)
        self.assertIn("step-by-step", TUTORIAL_OVERVIEW_PROMPT)
        self.assertIn("practical applications", TUTORIAL_OVERVIEW_PROMPT)
        self.assertIn("Code_Snippet", TUTORIAL_OVERVIEW_PROMPT)

    def test_general_overview_prompt_content(self):
        """Test that general overview prompt contains general-specific instructions."""
        self.assertIn("general audience", GENERAL_OVERVIEW_PROMPT)
        self.assertIn("main points", GENERAL_OVERVIEW_PROMPT)
        self.assertIn("key takeaways", GENERAL_OVERVIEW_PROMPT)
        self.assertIn("accessible", GENERAL_OVERVIEW_PROMPT)
        self.assertIn("Code_Snippet", GENERAL_OVERVIEW_PROMPT)

    @patch('backend.utils.overview_generators._generate_overview_openrouter')
    def test_generate_research_overview_success(self, mock_openrouter):
        """Test successful research overview generation."""
        mock_openrouter.return_value = json.dumps(self.mock_research_script_response)
        
        result = generate_research_overview(
            markdown=self.sample_research_content,
            paper_id="2024.12345",
            method="openrouter"
        )
        
        self.assertEqual(result, json.dumps(self.mock_research_script_response))
        mock_openrouter.assert_called_once_with(self.sample_research_content, "research", "2024.12345")

    @patch('backend.utils.overview_generators._generate_overview_openrouter')
    def test_generate_tutorial_overview_success(self, mock_openrouter):
        """Test successful tutorial overview generation."""
        mock_openrouter.return_value = json.dumps(self.mock_script_response)
        
        result = generate_tutorial_overview(
            markdown=self.sample_tutorial_content,
            url="https://example.com/tutorial",
            method="openrouter"
        )
        
        self.assertEqual(result, json.dumps(self.mock_script_response))
        mock_openrouter.assert_called_once_with(self.sample_tutorial_content, "tutorial", "tutorial_content")

    @patch('backend.utils.overview_generators._generate_overview_openrouter')
    def test_generate_general_overview_success(self, mock_openrouter):
        """Test successful general overview generation."""
        mock_openrouter.return_value = json.dumps(self.mock_script_response)
        
        result = generate_general_overview(
            markdown=self.sample_general_content,
            url="https://example.com/article",
            method="openrouter"
        )
        
        self.assertEqual(result, json.dumps(self.mock_script_response))
        mock_openrouter.assert_called_once_with(self.sample_general_content, "general", "general_content")

    def test_generate_research_overview_invalid_method(self):
        """Test research overview generation with invalid method."""
        with self.assertRaises(ValueError) as context:
            generate_research_overview(
                markdown=self.sample_research_content,
                paper_id="2024.12345",
                method="invalid"
            )
        self.assertIn("Invalid method: invalid", str(context.exception))

    def test_generate_tutorial_overview_invalid_method(self):
        """Test tutorial overview generation with invalid method."""
        with self.assertRaises(ValueError) as context:
            generate_tutorial_overview(
                markdown=self.sample_tutorial_content,
                url="https://example.com/tutorial",
                method="invalid"
            )
        self.assertIn("Invalid method: invalid", str(context.exception))

    def test_generate_general_overview_invalid_method(self):
        """Test general overview generation with invalid method."""
        with self.assertRaises(ValueError) as context:
            generate_general_overview(
                markdown=self.sample_general_content,
                url="https://example.com/article",
                method="invalid"
            )
        self.assertIn("Invalid method: invalid", str(context.exception))

    @patch('backend.utils.overview_generators.generate_research_overview')
    def test_generate_overview_by_type_research(self, mock_research):
        """Test generate_overview_by_type with research content."""
        mock_research.return_value = "research_script"
        
        result = generate_overview_by_type(
            content_type="research",
            markdown=self.sample_research_content,
            source_identifier="2024.12345",
            method="openrouter"
        )
        
        self.assertEqual(result, "research_script")
        mock_research.assert_called_once_with(self.sample_research_content, "2024.12345", "openrouter")

    @patch('backend.utils.overview_generators.generate_tutorial_overview')
    def test_generate_overview_by_type_tutorial(self, mock_tutorial):
        """Test generate_overview_by_type with tutorial content."""
        mock_tutorial.return_value = "tutorial_script"
        
        result = generate_overview_by_type(
            content_type="tutorial",
            markdown=self.sample_tutorial_content,
            source_identifier="https://example.com/tutorial",
            method="openrouter"
        )
        
        self.assertEqual(result, "tutorial_script")
        mock_tutorial.assert_called_once_with(self.sample_tutorial_content, "https://example.com/tutorial", "openrouter")

    @patch('backend.utils.overview_generators.generate_general_overview')
    def test_generate_overview_by_type_general(self, mock_general):
        """Test generate_overview_by_type with general content."""
        mock_general.return_value = "general_script"
        
        result = generate_overview_by_type(
            content_type="general",
            markdown=self.sample_general_content,
            source_identifier="https://example.com/article",
            method="openrouter"
        )
        
        self.assertEqual(result, "general_script")
        mock_general.assert_called_once_with(self.sample_general_content, "https://example.com/article", "openrouter")

    def test_generate_overview_by_type_invalid_content_type(self):
        """Test generate_overview_by_type with invalid content type."""
        with self.assertRaises(ValueError) as context:
            generate_overview_by_type(
                content_type="invalid",
                markdown=self.sample_general_content,
                source_identifier="https://example.com/article",
                method="openrouter"
            )
        self.assertIn("Invalid content_type: invalid", str(context.exception))

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    @patch('backend.utils.overview_generators.instructor')
    @patch('backend.utils.overview_generators.OpenAI')
    def test_generate_overview_openai_success(self, mock_openai_class, mock_instructor):
        """Test successful OpenAI overview generation."""
        # Mock the instructor client
        mock_client = Mock()
        mock_instructor.from_openai.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_client.chat.completions.create_with_completion.return_value = (mock_response, Mock())
        
        # Mock reconstruct_script
        with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
            mock_reconstruct.return_value = json.dumps(self.mock_research_script_response)
            
            result = _generate_overview_openai("test content", "research", "test_id")
            
            self.assertEqual(result, json.dumps(self.mock_research_script_response))
            mock_client.chat.completions.create_with_completion.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_overview_openai_missing_api_key(self):
        """Test OpenAI overview generation with missing API key."""
        with self.assertRaises(ValueError) as context:
            _generate_overview_openai("test content", "research", "test_id")
        self.assertIn("You need to set the OPENAI_API_KEY environment variable", str(context.exception))

    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'})
    @patch('backend.utils.overview_generators.instructor')
    @patch('backend.utils.overview_generators.OpenAI')
    def test_generate_overview_openrouter_success(self, mock_openai_class, mock_instructor):
        """Test successful OpenRouter overview generation."""
        # Mock the instructor client
        mock_client = Mock()
        mock_instructor.from_openai.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_client.chat.completions.create_with_completion.return_value = (mock_response, Mock())
        
        # Mock reconstruct_script
        with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
            mock_reconstruct.return_value = json.dumps(self.mock_script_response)
            
            result = _generate_overview_openrouter("test content", "tutorial", "tutorial_content")
            
            self.assertEqual(result, json.dumps(self.mock_script_response))
            mock_client.chat.completions.create_with_completion.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_overview_openrouter_missing_api_key(self):
        """Test OpenRouter overview generation with missing API key."""
        with self.assertRaises(ValueError) as context:
            _generate_overview_openrouter("test content", "tutorial", "tutorial_content")
        self.assertIn("You need to set the OPENROUTER_API_KEY environment variable", str(context.exception))

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
    @patch('backend.utils.overview_generators.genai')
    @patch('backend.utils.overview_generators.instructor')
    def test_generate_overview_gemini_success(self, mock_instructor, mock_genai):
        """Test successful Gemini overview generation."""
        # Mock genai configuration
        mock_genai.configure = Mock()
        
        # Mock the instructor client
        mock_client = Mock()
        mock_instructor.from_gemini.return_value = mock_client
        
        # Mock the response with usage metadata
        mock_response = Mock()
        mock_raw = Mock()
        mock_raw.usage_metadata.prompt_token_count = 1000
        mock_client.chat.completions.create_with_completion.return_value = (mock_response, mock_raw)
        
        # Mock reconstruct_script
        with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
            mock_reconstruct.return_value = json.dumps(self.mock_script_response)
            
            result = _generate_overview_gemini("test content", "general", "general_content")
            
            self.assertEqual(result, json.dumps(self.mock_script_response))
            mock_client.chat.completions.create_with_completion.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_overview_gemini_missing_api_key(self):
        """Test Gemini overview generation with missing API key."""
        with self.assertRaises(ValueError) as context:
            _generate_overview_gemini("test content", "general", "general_content")
        self.assertIn("You need to set the GEMINI_API_KEY environment variable", str(context.exception))

    @patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'})
    @patch('backend.utils.overview_generators.instructor')
    @patch('backend.utils.overview_generators.Groq')
    def test_generate_overview_groq_success(self, mock_groq_class, mock_instructor):
        """Test successful Groq overview generation."""
        # Mock the instructor client
        mock_client = Mock()
        mock_instructor.from_groq.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_client.chat.completions.create_with_completion.return_value = (mock_response, Mock())
        
        # Mock reconstruct_script
        with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
            mock_reconstruct.return_value = json.dumps(self.mock_research_script_response)
            
            result = _generate_overview_groq("test content", "research", "test_id")
            
            self.assertEqual(result, json.dumps(self.mock_research_script_response))
            mock_client.chat.completions.create_with_completion.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_overview_groq_missing_api_key(self):
        """Test Groq overview generation with missing API key."""
        with self.assertRaises(ValueError) as context:
            _generate_overview_groq("test content", "research", "test_id")
        self.assertIn("You need to set the GROQ_API_KEY environment variable", str(context.exception))

    @patch('backend.utils.overview_generators._generate_overview_openai')
    def test_all_methods_supported(self, mock_openai):
        """Test that all AI provider methods are supported."""
        mock_openai.return_value = "test_script"
        
        # Test all methods for research overview
        methods = ["openai", "gemini", "groq", "openrouter"]
        
        for method in methods:
            with patch(f'backend.utils.overview_generators._generate_overview_{method}') as mock_method:
                mock_method.return_value = f"{method}_script"
                
                result = generate_research_overview(
                    markdown=self.sample_research_content,
                    paper_id="test_id",
                    method=method
                )
                
                self.assertEqual(result, f"{method}_script")
                mock_method.assert_called_once_with(self.sample_research_content, "research", "test_id")

    def test_prompt_selection_logic(self):
        """Test that correct prompts are selected based on content type."""
        with patch('backend.utils.overview_generators.instructor') as mock_instructor:
            with patch('backend.utils.overview_generators.OpenAI'):
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
                    mock_client = Mock()
                    mock_instructor.from_openai.return_value = mock_client
                    mock_client.chat.completions.create_with_completion.return_value = (Mock(), Mock())
                    
                    with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
                        mock_reconstruct.return_value = "test_script"
                        
                        # Test research prompt selection
                        _generate_overview_openai("content", "research", "id")
                        call_args = mock_client.chat.completions.create_with_completion.call_args
                        self.assertIn(RESEARCH_OVERVIEW_PROMPT, call_args[1]['messages'][0]['content'])
                        
                        # Test tutorial prompt selection
                        _generate_overview_openai("content", "tutorial", "id")
                        call_args = mock_client.chat.completions.create_with_completion.call_args
                        self.assertIn(TUTORIAL_OVERVIEW_PROMPT, call_args[1]['messages'][0]['content'])
                        
                        # Test general prompt selection
                        _generate_overview_openai("content", "general", "id")
                        call_args = mock_client.chat.completions.create_with_completion.call_args
                        self.assertIn(GENERAL_OVERVIEW_PROMPT, call_args[1]['messages'][0]['content'])

    @patch('backend.utils.overview_generators.logger')
    def test_logging_behavior(self, mock_logger):
        """Test that appropriate logging occurs during overview generation."""
        with patch('backend.utils.overview_generators._generate_overview_openrouter') as mock_openrouter:
            mock_openrouter.return_value = "test_script"
            
            generate_research_overview(self.sample_research_content, "test_id", "openrouter")
            
            mock_logger.info.assert_called_with("Generating research overview for paper test_id using openrouter")

    def test_error_handling_in_generation(self):
        """Test error handling during script generation."""
        with patch('backend.utils.overview_generators.instructor') as mock_instructor:
            with patch('backend.utils.overview_generators.OpenAI'):
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
                    mock_client = Mock()
                    mock_instructor.from_openai.return_value = mock_client
                    mock_client.chat.completions.create_with_completion.return_value = (Mock(), Mock())
                    
                    # Mock reconstruct_script to raise an exception
                    with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
                        mock_reconstruct.side_effect = Exception("Reconstruction failed")
                        
                        with self.assertRaises(ValueError) as context:
                            _generate_overview_openai("content", "research", "id")
                        self.assertIn("The model failed the script generation", str(context.exception))

    def test_content_type_specific_identifiers(self):
        """Test that content type specific identifiers are used correctly."""
        with patch('backend.utils.overview_generators._generate_overview_openrouter') as mock_openrouter:
            mock_openrouter.return_value = "test_script"
            
            # Research should use the provided paper_id
            generate_research_overview("content", "2024.12345", "openrouter")
            mock_openrouter.assert_called_with("content", "research", "2024.12345")
            
            # Tutorial should use "tutorial_content"
            generate_tutorial_overview("content", "https://example.com", "openrouter")
            mock_openrouter.assert_called_with("content", "tutorial", "tutorial_content")
            
            # General should use "general_content"
            generate_general_overview("content", "https://example.com", "openrouter")
            mock_openrouter.assert_called_with("content", "general", "general_content")

    def test_specialized_schemas_usage(self):
        """Test that specialized schemas are used for tutorial and general content."""
        with patch('backend.utils.overview_generators.instructor') as mock_instructor:
            with patch('backend.utils.overview_generators.OpenAI'):
                with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
                    mock_client = Mock()
                    mock_instructor.from_openai.return_value = mock_client
                    mock_client.chat.completions.create_with_completion.return_value = (Mock(), Mock())
                    
                    with patch('backend.utils.overview_generators.reconstruct_script') as mock_reconstruct:
                        mock_reconstruct.return_value = "test_script"
                        
                        # Test that tutorial content uses tutorial schema
                        with patch('backend.utils.overview_generators.generate_tutorial_model_with_context_check') as mock_tutorial_schema:
                            mock_tutorial_schema.return_value = Mock()
                            _generate_overview_openrouter("content", "tutorial", "tutorial_content")
                            mock_tutorial_schema.assert_called_once_with("tutorial_content", "content")
                        
                        # Test that general content uses general schema
                        with patch('backend.utils.overview_generators.generate_general_model_with_context_check') as mock_general_schema:
                            mock_general_schema.return_value = Mock()
                            _generate_overview_openrouter("content", "general", "general_content")
                            mock_general_schema.assert_called_once_with("general_content", "content")
                        
                        # Test that research content uses research schema
                        with patch('backend.utils.overview_generators.generate_model_with_context_check') as mock_research_schema:
                            mock_research_schema.return_value = Mock()
                            _generate_overview_openrouter("content", "research", "2024.12345")
                            mock_research_schema.assert_called_once_with("2024.12345", "content")

    def test_code_snippet_component_support(self):
        """Test that Code_Snippet components are supported in tutorial and general prompts."""
        # Test tutorial prompt includes Code_Snippet
        self.assertIn("Code_Snippet", TUTORIAL_OVERVIEW_PROMPT)
        self.assertIn("code examples", TUTORIAL_OVERVIEW_PROMPT.lower())
        
        # Test general prompt includes Code_Snippet
        self.assertIn("Code_Snippet", GENERAL_OVERVIEW_PROMPT)
        self.assertIn("code examples", GENERAL_OVERVIEW_PROMPT.lower())
        
        # Test research prompt does NOT include Code_Snippet (it's research-focused)
        self.assertNotIn("Code_Snippet", RESEARCH_OVERVIEW_PROMPT)


if __name__ == "__main__":
    unittest.main()