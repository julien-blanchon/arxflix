from typing import Literal
from openai import OpenAI
from  backend.schemas.script import generate_model_with_context_check, reconstruct_script
import instructor
import requests
import os

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
    - paper_id: The id of the paper
    - target_duration_minutes : The target duration of the video
    - components : a list of component (component_type, content, position)
        - You should follow this format for each component: Text, Figure, Equation and Headline
        - Figure, Equation (latex) and Headline will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
        - The Text will be spoken by a narrator and caption in the video.
        - Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
        - For Equation: Don't use $ or [, the latex context is automatically detected.
        - For Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
        - Don't hallucinate figures.
        - Figure starts by https://arxiv.org/html/xxxx.aaaa/  where xxxx.aaaa is the id of the paper. Each Figure is followed by a text which explains it point.
</format_instructions>

<exemple_of_Firgure>
![](arxiv.org/x1.png) should be rendered as https://arxiv.org/html/xxxx.aaaa/x1.png   where xxxx.aaaa is the id of the paper
![](extracted/5604403/figure/moe_intro.png) should be rendered as https://arxiv.org/html/2405.11273/extracted/5604403/figure/moe_intro.png  where 2405.11273 is the id of the paper
</exemple_of_Firgure>



Here is an exampl of what you need to produce for paper id 2405.11273:
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
            "content": "https://arxiv.org/html/2405.11273/extracted/5604403/figure/moe_intro.png",
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

Attention : The paper_id in the precedent instruction are just exemples. Don't confuse it with the correct paper ID you ll receve.

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
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not OPENAI_API_KEY:
        raise ValueError("You need to set the OPENAI_API_KEY environment variable.")

    openai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":  "Here is the paper I want you to generate a script from : " + paper},
        ],
        response_model=generate_model_with_context_check(paper_id),
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


def process_script(method: Literal["openai"], paper_markdown: str, paper_id : str) -> str:
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
    if method == "openai":
        return _process_script_gpt(paper_markdown,paper_id)
    else:
        raise ValueError("Invalid method. Please choose 'openai'.")
