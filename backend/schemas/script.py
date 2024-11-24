from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal, Union
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class ScriptComponentType(str, Enum):
    TEXT = "Text"
    FIGURE = "Figure"
    EQUATION = "Equation"
    HEADLINE = "Headline"

class ScriptComponent(BaseModel):
    component_type: ScriptComponentType = Field(
        ...,
        description="Type of script component",
        examples=["Text", "Figure", "Equation", "Headline"]
    )
    content: str = Field(
        ...,
        description="Content of the component",
        examples=[
            "Welcome to Arxflix! Today we'll explore a fascinating paper about AI.",
            "https://arxiv.org/html/2405.11273/extracted/5604403/figure/moe_intro.png",
            "E = mc^2",
            "Groundbreaking Research in AI"
        ]
    )
    position: int = Field(
        ...,
        ge=0,
        description="Position in the script (0-based index)",
        examples=[0, 1, 2, 3]
    )

    @model_validator(mode='after')
    def validate_content(cls, values):
        component_type = values.component_type
        logger.info(f"Validating script structure")
        
        if component_type == ScriptComponentType.FIGURE:
            pattern = r'^https://arxiv\.org/html/\d{4}\.\d{4,5}(/.*)?$'
            if not re.match(pattern, values.content):
                raise ValueError("Figure URL must start with 'https://arxiv.org/html/' followed by paper ID")
        
        elif component_type == ScriptComponentType.EQUATION:
            if '$' in values.content or r'\[' in v or '\n' in v:
                raise ValueError("Equation must not contain $, \\[, or multiple lines")
        
        elif component_type == ScriptComponentType.TEXT:
            if re.search(r'^\s*[-\d]\.\s', values.content):
                raise ValueError("Text must not contain markdown listing patterns")
            
            if len(values.content.strip()) < 10:
                raise ValueError("Text component must contain at least 10 characters")
        
        return values

def generate_model_with_context_check(paper_id : str ):
    class ArxflixScript(BaseModel):
        title: str = Field(
            ...,
            description="Title of the research paper",
            examples=[
                "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts",
                "Attention Is All You Need",
                "BERT: Pre-training of Deep Bidirectional Transformers"
            ]
        )
        paper_id: str = Field(
            ...,
            description=f"ArXiv paper ID (e.g., '2405.11273')",
            examples=["2405.11273", "1706.03762", "1810.04805"]
        )
        target_duration_minutes: float = Field(
            ...,
            ge=0,
            le=6,
            description="Target video duration in minutes",
            examples=[5.0, 5.5, 6.0]
        )
        components: List[ScriptComponent] = Field(
            ...,
            description="List of script components",
            examples=[[
                {
                    "component_type": "Headline",
                    "content": "GPT-4: Advanced Language Modeling",
                    "position": 0
                },
                {
                    "component_type": "Text",
                    "content": "Today we're exploring the revolutionary GPT-4 model.",
                    "position": 1
                },
                {
                    "component_type": "Figure",
                    "content": "https://arxiv.org/html/2405.11273/figure1.png",
                    "position": 2
                }
            ]]
        )

        @model_validator(mode='after')
        def validate_script_structure(cls,values):
            errors = []
            logger.info(f"Validating script structure for paper_id: {paper_id}")

            components = values.components

            

            if not components:
                errors.append(ValueError("Script must contain at least one component"))

            if values.paper_id != paper_id:
                logger.warning(f"Paper ID mismatch: expected {paper_id}, got {values.paper_id}, correcting")
                errors.append(ValueError(f"The paper id is {paper_id}, you wrote a wrong one, correct it everywhere"))
                
            else:
                sorted_components = sorted(components, key=lambda x: x.position)
                
                positions = [comp.position for comp in sorted_components]
                if positions != list(range(len(positions))):
                    errors.append(ValueError("Component positions must be consecutive integers starting from 0"))

                if sorted_components[0].component_type != ScriptComponentType.HEADLINE:
                    errors.append(ValueError("Script must start with a Headline component"))
                
                for i in range(1, len(sorted_components)):
                    if (sorted_components[i].component_type == sorted_components[i-1].component_type and 
                        sorted_components[i].component_type != ScriptComponentType.TEXT):
                        errors.append(ValueError(f"Consecutive {sorted_components[i].component_type} components are not allowed"))

                values.components = sorted_components
            #set replace paper id in the figure link with values.paper_id, knowing link is of format https://arxiv.org/html/2405.11273/figure1.png    
            for comp in values.components:
                if comp.component_type == ScriptComponentType.FIGURE:
                    comp.content = comp.content.replace(comp.content.split('/')[4], values.paper_id)
            if errors:
                raise ValueError(errors)
            return values
    return ArxflixScript


def parse_script(raw_script: str, paper_id: str) -> BaseModel:
    """
    Parse raw script text into ArxflixScript model.
    
    Args:
        raw_script (str): Raw script text with \component format
        paper_id (str): ArXiv paper ID
        
    Returns:
        ArxflixScript: Validated script model
    
    Example:
        >>> raw_script = '''
        ... \Headline: Understanding GPT-4
        ... \Text: Welcome to this exciting paper review!
        ... \Figure: https://arxiv.org/html/2405.11273/figure1.png
        ... '''
        >>> script = parse_script(raw_script, "2405.11273")
    """
    lines = raw_script.strip().split('\n')
    components = []
    position = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        if not line.startswith('\\'):
            raise ValueError(f"Invalid line format: {line}")
            
        component_parts = line[1:].split(':', 1)
        if len(component_parts) != 2:
            raise ValueError(f"Invalid component format: {line}")
            
        component_type, content = component_parts
        components.append(ScriptComponent(
            component_type=component_type,
            content=content.strip(),
            position=position
        ))
        position += 1
    
    title = next((comp.content for comp in components 
                 if comp.component_type == ScriptComponentType.HEADLINE), "")
    
    return generate_model_with_context_check(paper_id)(
        title=title,
        paper_id=paper_id,
        target_duration_minutes=5.0,
        components=components
    )

def reconstruct_script(script: BaseModel) -> str:
    """
    Reconstruct the script text from ArxflixScript model.
    
    Args:
        script (ArxflixScript): Validated script model
        
    Returns:
        str: Formatted script text
    
    Example:
        >>> script = ArxflixScript(
        ...     title="Understanding GPT-4",
        ...     paper_id="2405.11273",
        ...     target_duration_minutes=5.0,
        ...     components=[
        ...         ScriptComponent(component_type="Headline", content="Understanding GPT-4", position=0),
        ...         ScriptComponent(component_type="Text", content="Welcome to this review!", position=1)
        ...     ]
        ... )
        >>> print(reconstruct_script(script))
        \Headline: Understanding GPT-4
        \Text: Welcome to this review!
    """
    return '\n'.join(f"\\{comp.component_type.value}: {comp.content}" 
                    for comp in script.components)