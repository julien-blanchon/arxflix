from typing import Literal
from openai import OpenAI
from  backend.schemas.script import generate_model_with_context_check, reconstruct_script
import instructor
import requests
import os
import google.generativeai as genai
import logging
from groq import Groq

logger = logging.getLogger(__name__)

import re
def replace_keys_with_values(text, dict_list):
  """
  Replaces keys found in a text with their corresponding values from a list of dictionaries.

  Args:
    text: The input text string.
    dict_list: A list of dictionaries where keys are patterns to search for in the text 
               and values are the replacements.

  Returns:
    The modified text with keys replaced by values.
  """

  # Combine all dictionaries into a single dictionary for efficiency
  combined_dict = {}
  for d in dict_list:
    combined_dict.update(d)

  # Sort keys by length in descending order to handle overlapping keys correctly
  sorted_keys = sorted(combined_dict.keys(), key=len, reverse=True)

  # Build a regular expression pattern to match any of the keys
  # Escape special characters in keys for use in regex
  pattern = re.compile("|".join(map(re.escape, sorted_keys)))

  # Perform the replacement using re.sub with a lambda function
  modified_text = pattern.sub(lambda match: combined_dict[match.group(0)], text)

  return modified_text

def adjust_links(text_md : str, paper_id : str):

    def get_link(link,paper_id):
        if 'ar5iv.labs.arxiv.org' in link:
            return '![]('+link.replace('![](','https://').replace(')','')+')'
        elif f'https:/arxiv.org/html/{paper_id}/'  in link:
            return '![]('+link.replace('![](',f'https://arxiv.org/html/{paper_id}/').replace(')','')+')'
        elif '(arxiv.org' in link:
            return '![]('+link.replace('![](arxiv.org',f'https://arxiv.org/html/{paper_id}').replace(')','')+')'
        else:
            return '![]('+link.replace('![](',f'https://arxiv.org/html/{paper_id}/').replace(')','')+')'

    links  = [{line : get_link(line,paper_id)} for line in text_md.split('\n') if '![](' in line]

    return replace_keys_with_values(text_md, links)



SYSTEM_PROMPT = r"""
<context>
You're Arxflix an AI Researcher and Content Creator on Youtube who specializes in summarizing academic papers.
The video will be uploaded on YouTube and is intended for a research-focused audience of academics, students, and professionals of the field of deep learning. 
</context>

<goal>
Generate a script for a mid-short video (5-6 minutes or less than 6000 words) on the research paper you will receve.
</goal>


<style_instructions>
The script should be engaging, clear, and concise, effectively communicating the content of the paper. 
The video should give a good overview of the paper in the least amount of time possible, with short sentences that fit well for a dynamic Youtube video.
The overall goal of the video is to make research papers more accessible and understandable to a wider audience, while maintaining academic rigor.
</style_instructions>

<format_instructions>
The script sould be formated following the followings rules below:
- Your ouput is a JSON with the following keys :
    - title: The title of the video.
    - paper_id: The id of the paper (e.g., '2405.11273') explicitly mensionned in the paper
    - target_duration_minutes : The target duration of the video
    - components : a list of component (component_type, content, position)
        - You should follow this format for each component: Text, Figure, Equation and Headline
        - The only autorized component_type are : Text, Figure, Equation and Headline
        - Figure, Equation (latex) and Headline will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
        - The Text will be spoken by a narrator and caption in the video.
        - Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
        - For Equation: Don't use $ or [, the latex context is automatically detected.
        - For Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
        - Don't hallucinate figures.
        - Don't forget to maintain https:// as it is in the link.
</format_instructions>

<example_figures>
![](https://arxiv.org/html/2405.11273/multi_od/files1/figure/moe_intro.png) is rendered as "https://arxiv.org/html/2405.11273/multi_od/files1/figure/moe_intro.png".
![](ar5iv.labs.arxiv.org//html/5643.43534/assets/x5.png) is rendered as "ar5iv.labs.arxiv.org//html/5643.43534/assets/x5.png"
<example_figures>
Attention : 
- The paper_id in the precedent instruction are just exemples. Don't confuse it with the correct paper ID you ll receve.
- Only extract figure that are present in the paper. Don't use the exemple links. 
- keep the full link of the figure in the figure content value
- Do not forget 'https://' a the start of the figure link.
- Always include at least one figure if present in the text. Viewers like when the video is animated and well commented. 3blue1brown Style


Here is an example of what you need to produce for paper id 2405.11273: 
<exemple>
{
    "title": "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts",
    "paper_id": "2405.11273",
    "target_duration_minutes": 5.5,
    "components": [
        {
            "component_type": "Headline",
            "content": "Uni-MoE: Revolutionary Multimodal Architecture",
            "position": 0
        },
        {
            "component_type": "Text",
            "content": "Welcome back to Arxflix! Today, we’re diving into an exciting new paper titled "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts". This research addresses the challenge of efficiently scaling multimodal large language models (MLLMs) to handle a variety of data types like text, images, audio, and video.",
            "position": 1
        },
        {
            "component_type": "Figure",
            "content": "https://arxiv.org/html/2405.11273/multi_od/files1/figure/moe_intro.png",
            "position": 2
        },
        {
            "component_type": "Text",
            "content": "Here’s a snapshot of the Uni-MoE model, illustrating its ability to handle multiple modalities using the Mixture of Experts (MoE) architecture. Let’s break down the main points of this paper.",
            "position": 3
        },
        {
            "component_type": "Headline",
            "content": "The Problem with Traditional Scaling",
            "position": 4
        },
        {
            "component_type": "Text",
            "content": "Scaling multimodal models traditionally incurs high computational costs. Conventional models process each input with all model parameters, leading to dense and inefficient computations.",
            "position": 5
        },
        {
            "component_type": "Text",
            "content": "Enter the Mixture of Experts (MoE). Unlike dense models, MoE activates only a subset of experts for each input. This sparse activation reduces computational overhead while maintaining performance.",
            "position": 6
        },
        {
            "component_type": "Text",
            "content": "Previous works have used MoE in text and image-text models but limited their scope to fewer experts and modalities. This paper pioneers a unified MLLM leveraging MoE across multiple modalities.",
            "position": 7
        },
        ...
    ]
}
</exemple>


Your output is a JSON with the following structure : 

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

SYSTEM_PROMPT_NO_LINK = r"""
<context>
You're Arxflix an AI Researcher and Content Creator on Youtube who specializes in summarizing academic papers.
The video will be uploaded on YouTube and is intended for a research-focused audience of academics, students, and professionals of the field of deep learning. 
</context>

<goal>
Generate a script for a mid-short video (5-6 minutes or less than 6000 words) on the research paper you will receve.
</goal>


<style_instructions>
The script should be engaging, clear, and concise, effectively communicating the content of the paper. 
The video should give a good overview of the paper in the least amount of time possible, with short sentences that fit well for a dynamic Youtube video.
The overall goal of the video is to make research papers more accessible and understandable to a wider audience, while maintaining academic rigor.
</style_instructions>

<format_instructions>
The script sould be formated following the followings rules below:
- Your ouput is a JSON with the following keys :
    - title: The title of the video.
    - paper_id: The id of the paper (e.g., '2405.11273') explicitly mensionned in the paper
    - target_duration_minutes : The target duration of the video
    - components : a list of component (component_type, content, position)
        - You should follow this format for each component: Text, Figure, Equation and Headline
        - The only autorized component_type are : Text, Figure, Equation and Headline
        - Figure, Equation (latex) and Headline will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
        - The Text will be spoken by a narrator and caption in the video.
        - Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
        - For Equation: Don't use $ or [, the latex context is automatically detected.
        - For Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
        - Don't hallucinate figures.
        - Don't forget to keep the full path of the figure in the figure content value.
</format_instructions>

<example_figures>
/Users/davidperso/projects/arxflix/images/moe_intro.png
<example_figures>
Attention : 


Here is an example of what you need to produce for paper id 2405.11273: 
<exemple>
{
    "title": "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts",
    "paper_id": "2405.11273",
    "target_duration_minutes": 5.5,
    "components": [
        {
            "component_type": "Headline",
            "content": "Uni-MoE: Revolutionary Multimodal Architecture",
            "position": 0
        },
        {
            "component_type": "Text",
            "content": "Welcome back to Arxflix! Today, we’re diving into an exciting new paper titled "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts". This research addresses the challenge of efficiently scaling multimodal large language models (MLLMs) to handle a variety of data types like text, images, audio, and video.",
            "position": 1
        },
        {
            "component_type": "Figure",
            "content": "/Users/davidperso/projects/arxflix/images/moe_intro.png",
            "position": 2
        },
        {
            "component_type": "Text",
            "content": "Here’s a snapshot of the Uni-MoE model, illustrating its ability to handle multiple modalities using the Mixture of Experts (MoE) architecture. Let’s break down the main points of this paper.",
            "position": 3
        },
        {
            "component_type": "Headline",
            "content": "The Problem with Traditional Scaling",
            "position": 4
        },
        {
            "component_type": "Text",
            "content": "Scaling multimodal models traditionally incurs high computational costs. Conventional models process each input with all model parameters, leading to dense and inefficient computations.",
            "position": 5
        },
        {
            "component_type": "Text",
            "content": "Enter the Mixture of Experts (MoE). Unlike dense models, MoE activates only a subset of experts for each input. This sparse activation reduces computational overhead while maintaining performance.",
            "position": 6
        },
        {
            "component_type": "Text",
            "content": "Previous works have used MoE in text and image-text models but limited their scope to fewer experts and modalities. This paper pioneers a unified MLLM leveraging MoE across multiple modalities.",
            "position": 7
        },
        ...
    ]
}
</exemple>


Your output is a JSON with the following structure : 

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


def _correct_result_link(script: str, url: str) -> str:
    """Correct generated links in a research paper script.

    Parameters:
    - script: str
        The script of a research paper.
    - url: str
        The base URL of the research paper (can contain "/html/").

    Returns:
    - str
        The corrected script with valid image links.
    """
    # handle non-arXiv links
    if "ar5iv" not in url:
        tmp_url = url.split("/")
        url = (
            "https://ar5iv.labs.arxiv.org/html/" + tmp_url[-1]
            if tmp_url[-1] != ""
            else "https://ar5iv.labs.arxiv.org/html/" + tmp_url[-2]
        )

    split_script = script.split("n")

    for line_idx, line in enumerate(split_script):
        if r"Figure: " in line and not line.startswith("https"):
            tmp_line = line.replace(r"Figure: ", "")

            # Construct the potential figure URL
            if "/html/" in tmp_line:
                modified_base_url = url.split("/html/")[0]
                figure_url = f"{modified_base_url}{tmp_line}"
            else:
                figure_url = f"{url if url.endswith('/') else url+'/'}{tmp_line if tmp_line[0] != '/' else tmp_line[1:]}"

            try:
                # Check if the URL leads to an image (PNG)
                response = requests.head(figure_url)
                if response.status_code == 200 and "image/png" in response.headers.get(
                    "Content-Type", ""
                ):
                    split_script[line_idx] = r"Figure: " + figure_url
                else:
                    # Remove "ar5iv.labs." and try again
                    figure_url = figure_url.replace("ar5iv.labs.", "")
                    response = requests.head(figure_url)
                    if (
                        response.status_code == 200
                        and "image/png" in response.headers.get("Content-Type", "")
                    ):
                        split_script[line_idx] = r"Figure: " + figure_url
            except requests.exceptions.RequestException:
                # If the request fails, leave the link as is (or handle the error as you prefer)
                pass

    return "n".join(split_script)


def _process_script_gpt(paper: str, paper_id:str) -> str:
    """Generate a video script for a research paper using OpenAI's GPT-4o model.

    Parameters
    ----------
    paper : str
        A research paper in markdown format. (For the moment, it's HTML)

    Returns
    -------
    str
        The generated video script.

    Raises
    ------
    ValueError
        If no result is returned from OpenAI.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

    if not OPENAI_API_KEY:
        raise ValueError("You need to set the OPENAI_API_KEY environment variable.")

    

    openai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":  f"Here is the paper I want you to generate a script from, its paper_id is {paper_id} : " + paper},
        ],
        response_model=generate_model_with_context_check(paper_id,paper),
        temperature=0,
        max_retries=3
    )

    try :
        result = reconstruct_script(response)
    except Exception as e:
        print(e)
        raise ValueError(f"The model failed the script generation:  {e}")
    # result = _correct_result_link(result, url)
    return result



def _process_script_groq(paper: str, paper_id:str) -> str:
    """Generate a video script for a research paper.

    Parameters
    ----------
    paper : str
        A research paper in markdown format. (For the moment, it's HTML)

    Returns
    -------
    str
        The generated video script.

    Raises
    ------
    ValueError
        If no result is returned from OpenAI.
    """
    GROQ_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")

    if not GROQ_API_KEY:
        raise ValueError("You need to set the OPENAI_API_KEY environment variable.")

    

    openai_client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))
    response = openai_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":  f"Here is the paper I want you to generate a script from, its paper_id is {paper_id} : " + paper},
        ],
        response_model=generate_model_with_context_check(paper_id,paper),
        temperature=0,
        max_retries=3
    )

    try :
        result = reconstruct_script(response)
    except Exception as e:
        print(e)
        raise ValueError(f"The model failed the script generation:  {e}")
    # result = _correct_result_link(result, url)
    return result

def _process_script_open_source(paper: str, paper_id:str, end_point_base_url : str ) -> str:
    """Generate a video script for a research paper using OpenAI's GPT-4o model.

    Parameters
    ----------
    paper : str
        A research paper in markdown format. (For the moment, it's HTML)

    Returns
    -------
    str
        The generated video script.

    Raises
    ------
    ValueError
        If no result is returned from OpenAI.
    """



    openai_client = instructor.from_openai(OpenAI(api_key="not-needed",
                                                  base_url=end_point_base_url))
    response = openai_client.chat.completions.create(
        model="not-needed",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":  "Here is the paper I want you to generate a script from : " + paper},
        ],
        response_model=generate_model_with_context_check(paper_id,paper),
        temperature=0,
        max_retries=3
    )

    try :
        result = reconstruct_script(response)
    except Exception as e:
        print(e)
        raise ValueError(f"The model failed the script generation:  {e}")
    # result = _correct_result_link(result, url)
    return result




def _process_script_open_gemini(paper: str, paper_id:str, end_point_base_url : str = "https://generativelanguage.googleapis.com/v1beta/openai/") -> str:
    """Generate a video script for a research paper using OpenAI's GPT-4o model.

    Parameters
    ----------
    paper : str
        A research paper in markdown format. (For the moment, it's HTML)

    Returns
    -------
    str
        The generated video script.

    Raises
    ------
    ValueError
        If no result is returned from OpenAI.
    """


    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


    genai.configure(api_key=GEMINI_API_KEY)

    # Define safety settings
    safe = [
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    gemini_client = instructor.from_gemini(client=genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    safety_settings=safe,
    generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
    ),
    mode=instructor.Mode.GEMINI_JSON,)
    

    try :
        response,raw = gemini_client.chat.completions.create_with_completion(

        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_NO_LINK if paper_id == "paper_id" else SYSTEM_PROMPT},
            {"role": "user", "content": f"Here is the paper I want you to generate a script from, its paper_id is {paper_id} : " + paper},
        ],
        response_model=generate_model_with_context_check(paper_id,paper),
        max_retries=3
    )
        logger.warning(f"Number input_token : {raw.usage_metadata.prompt_token_count}")
        result = reconstruct_script(response)
    except Exception as e:
        print(e)
        raise ValueError(f"The model failed the script generation:  {e}")
    # result = _correct_result_link(result, url)
    return result


def process_script(method: Literal["openai", "local", "gemini", "groq"], paper_markdown: str, paper_id : str, end_point_base_url : str, from_pdf: bool=False) -> str:
    """Generate a video script for a research paper.

    Parameters
    ----------
    paper_markdown : str
        A research paper in markdown format.

    Returns
    -------
    str
        The generated video script.

    Raises
    ------
    ValueError
        If no result is returned from OpenAI.
    """
    if not from_pdf:
        pd_corrected_links = adjust_links(paper_markdown , paper_id )
    else:
        pd_corrected_links = paper_markdown
    if method == "openai":
        return _process_script_gpt(pd_corrected_links,paper_id)
    if method == "local":
        return _process_script_open_source(pd_corrected_links, paper_id, end_point_base_url)
    if method == "gemini":
        return _process_script_open_gemini(pd_corrected_links, paper_id, end_point_base_url)
    if method == "groq":
        return _process_script_groq(pd_corrected_links,paper_id)
    else:
        raise ValueError("Invalid method. Please choose 'openai'.")
