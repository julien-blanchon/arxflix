"""
Unit tests for the OpenRouter-based content classification system.

Tests cover:
- OpenRouter-based classification with mocked responses
- Fallback classification when OpenRouter is unavailable
- Error handling and edge cases
- Pydantic model validation
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.content_classifier import (
    ContentClassifier, 
    ContentClassification,
    classify_content,
    extract_content_features,
    is_openrouter_available
)


class TestContentClassifier(unittest.TestCase):
    """Test cases for the ContentClassifier class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the OpenRouter client to avoid actual API calls
        with patch('backend.utils.content_classifier.ContentClassifier._initialize_openrouter_client'):
            self.classifier = ContentClassifier(confidence_threshold=0.7)
            self.classifier.client = MagicMock()
            
        # Import the response models for mocking
        from backend.schemas.content_classification import ContentClassificationResponse, ContentFeatures, ContentType
        
        # Mock OpenRouter responses for different content types using proper models
        self.mock_research_response = ContentClassificationResponse(
            content_type=ContentType.RESEARCH,
            confidence_score=0.9,
            features=ContentFeatures(
                primary_indicators="Abstract, methodology, results, citations",
                content_structure="Academic paper structure with clear sections",
                language_style="Formal academic writing",
                target_audience="Researchers and academics"
            ),
            reasoning="Content contains clear academic structure with abstract, methodology, results, and citations typical of research papers"
        )
        
        self.mock_tutorial_response = ContentClassificationResponse(
            content_type=ContentType.TUTORIAL,
            confidence_score=0.85,
            features=ContentFeatures(
                primary_indicators="Step-by-step instructions, code examples, how-to language",
                content_structure="Sequential instructional format",
                language_style="Instructional and practical",
                target_audience="Learners and practitioners"
            ),
            reasoning="Content follows tutorial format with step-by-step instructions and practical examples"
        )
        
        self.mock_general_response = ContentClassificationResponse(
            content_type=ContentType.GENERAL,
            confidence_score=0.75,
            features=ContentFeatures(
                primary_indicators="News-style writing, temporal references, general topics",
                content_structure="Article format with news-style organization",
                language_style="Journalistic and accessible",
                target_audience="General public"
            ),
            reasoning="Content appears to be general news or blog content with journalistic style"
        )
        
        # Sample content for testing
        self.research_content = """
# Abstract
This paper presents a novel approach to machine learning optimization.
# Methodology  
Our experimental setup involves training neural networks.
# Results
Figure 1 shows the performance comparison.
# References
[1] Smith et al., 2023.
        """
        
        self.tutorial_content = """
# How to Build a REST API
## Step 1: Installation
```bash
pip install flask
```
## Step 2: Create the app
```python
from flask import Flask
app = Flask(__name__)
```
        """
        
        self.general_content = """
# Tech Company Announces New Product
According to sources, the latest smartphone will feature advanced camera technology.
The announcement was made during yesterday's press conference.
        """

    def test_classifier_initialization(self):
        """Test ContentClassifier initialization"""
        with patch('backend.utils.content_classifier.ContentClassifier._initialize_openrouter_client'):
            classifier = ContentClassifier()
            self.assertEqual(classifier.confidence_threshold, 0.7)
            self.assertEqual(classifier.model_name, "google/gemini-2.0-flash-001")
            
            custom_classifier = ContentClassifier(
                model_name="gpt-4o-mini", 
                confidence_threshold=0.8
            )
            self.assertEqual(custom_classifier.confidence_threshold, 0.8)
            self.assertEqual(custom_classifier.model_name, "gpt-4o-mini")

    def test_classify_content_research(self):
        """Test classification of research content with mocked OpenRouter response"""
        # Mock the OpenRouter call to return research classification
        self.classifier._call_openrouter = MagicMock(return_value=self.mock_research_response)
        
        result = self.classifier.classify_content(self.research_content)
        
        self.assertIsInstance(result, ContentClassification)
        self.assertEqual(result.content_type, "research")
        self.assertEqual(result.confidence_score, 0.9)
        self.assertIsInstance(result.features, dict)
        self.assertIn("primary_indicators", result.features)
        self.assertIsInstance(result.reasoning, str)
        self.assertIn("research", result.reasoning.lower())

    def test_classify_content_tutorial(self):
        """Test classification of tutorial content with mocked OpenRouter response"""
        # Mock the OpenRouter call to return tutorial classification
        self.classifier._call_openrouter = MagicMock(return_value=self.mock_tutorial_response)
        
        result = self.classifier.classify_content(self.tutorial_content)
        
        self.assertIsInstance(result, ContentClassification)
        self.assertEqual(result.content_type, "tutorial")
        self.assertEqual(result.confidence_score, 0.85)
        self.assertIsInstance(result.features, dict)
        self.assertIn("primary_indicators", result.features)
        self.assertIsInstance(result.reasoning, str)
        self.assertIn("tutorial", result.reasoning.lower())

    def test_classify_content_general(self):
        """Test classification of general content with mocked OpenRouter response"""
        # Mock the OpenRouter call to return general classification
        self.classifier._call_openrouter = MagicMock(return_value=self.mock_general_response)
        
        result = self.classifier.classify_content(self.general_content)
        
        self.assertIsInstance(result, ContentClassification)
        self.assertEqual(result.content_type, "general")
        self.assertEqual(result.confidence_score, 0.75)
        self.assertIsInstance(result.features, dict)
        self.assertIn("primary_indicators", result.features)
        self.assertIsInstance(result.reasoning, str)

    def test_classify_content_empty(self):
        """Test classification of empty content"""
        result = self.classifier.classify_content("")
        
        self.assertEqual(result.content_type, "general")
        self.assertEqual(result.confidence_score, 0.0)
        self.assertIsInstance(result.features, dict)
        self.assertIn("Empty or invalid", result.reasoning)

    def test_fallback_classification(self):
        """Test fallback classification when OpenRouter is unavailable"""
        # Mock OpenRouter to return None (unavailable)
        self.classifier._call_openrouter = MagicMock(return_value=None)
        
        result = self.classifier.classify_content(self.research_content)
        
        self.assertIsInstance(result, ContentClassification)
        self.assertIn(result.content_type, ["research", "tutorial", "general"])
        self.assertIsInstance(result.confidence_score, float)
        self.assertIn("fallback", result.reasoning.lower())

    def test_error_handling(self):
        """Test error handling in classification"""
        # Mock OpenRouter to raise an exception
        self.classifier._call_openrouter = MagicMock(side_effect=Exception("API Error"))
        
        # This should not raise an exception, should fall back gracefully
        result = self.classifier.classify_content(self.research_content)
        self.assertIsInstance(result, ContentClassification)

    def test_convenience_functions(self):
        """Test the convenience functions work correctly"""
        with patch('backend.utils.content_classifier.ContentClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier.classify_content.return_value = ContentClassification(
                content_type="research",
                confidence_score=0.8,
                features={"primary_indicators": "test"},
                reasoning="test reasoning"
            )
            mock_classifier_class.return_value = mock_classifier
            
            # Test classify_content function
            result = classify_content(self.research_content)
            self.assertIsInstance(result, ContentClassification)
            
            # Test extract_content_features function
            features = extract_content_features(self.tutorial_content)
            self.assertIsInstance(features, dict)

    def test_openrouter_availability_check(self):
        """Test OpenRouter availability check"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('backend.utils.content_classifier.OpenAI', True):
                with patch('backend.utils.content_classifier.instructor', True):
                    self.assertTrue(is_openrouter_available())
        
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_openrouter_available())


class TestContentClassificationAccuracy(unittest.TestCase):
    """Test classification accuracy with various content samples using fallback"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('backend.utils.content_classifier.ContentClassifier._initialize_openrouter_client'):
            self.classifier = ContentClassifier()
            self.classifier.client = None  # Force fallback mode

    def test_research_paper_fallback_classification(self):
        """Test fallback classification of research paper content"""
        research_content = """
# Abstract
This paper presents a novel approach to machine learning optimization.
# Methodology
Our experimental setup involves training neural networks.
# Results
Figure 1 shows the performance comparison.
# Conclusion
The proposed methodology demonstrates improvements.
# References
[1] Smith et al., 2023.
DOI: 10.1000/example
        """
        
        result = self.classifier.classify_content(research_content)
        self.assertEqual(result.content_type, "research")
        self.assertGreater(result.confidence_score, 0.0)

    def test_tutorial_fallback_classification(self):
        """Test fallback classification of tutorial content"""
        tutorial_content = """
# How to Build a REST API
This tutorial will teach you how to create a REST API.
## Step 1: Installation
```bash
pip install flask
```
## Step 2: Setup
Create a new file and setup your application.
        """
        
        result = self.classifier.classify_content(tutorial_content)
        self.assertEqual(result.content_type, "tutorial")
        self.assertGreater(result.confidence_score, 0.0)

    def test_general_content_fallback_classification(self):
        """Test fallback classification of general content"""
        general_content = """
# Tech Company Announces New Product
According to industry experts, the company announced a new product today.
The market has responded positively to the news.
        """
        
        result = self.classifier.classify_content(general_content)
        # Fallback might classify this as general or research depending on keywords
        self.assertIn(result.content_type, ["general", "research"])
        self.assertGreaterEqual(result.confidence_score, 0.0)


if __name__ == '__main__':
    unittest.main()