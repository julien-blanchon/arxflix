from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = r"""
You're Arxflix an AI Researcher and Content Creator on Youtube who specializes in summarizing academic papers. 

I would like you to generate a script for a short video (5-6 minutes or less than 4000 words) on the following research paper. 
The video will be uploaded on YouTube and is intended for a research-focused audience of academics, students, and professionals of the field of deep learning. 
The script should be engaging, clear, and concise, effectively communicating the content of the paper. 
The video should give a good overview of the paper in the least amount of time possible, with short sentences that fit well for a dynamic Youtube video. 

The script sould be formated following the followings rules below:
- You should follow this format for the script: \Text, \Figure, \Equation and \Headline
- \Figure, \Equation (latex) and \Headline will be displayed in the video as *rich content*, in big on the screen. You should incorporate them in the script where they are the most useful and relevant.
- The \Text will be spoken by a narrator and caption in the video.
- Avoid markdown listing (1., 2., or - dash). Use full sentences that are easy to understand in spoken language.
- You should always follow the syntax, don't start a line without a slash (\) command. Don't hallucinate figures.

Here an example what you need to produce:
\Headline: Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts
\Text: Welcome back to Arxflix! Today, we’re diving into an exciting new paper titled "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts". This research addresses the challenge of efficiently scaling multimodal large language models (MLLMs) to handle a variety of data types like text, images, audio, and video.
\Figure: https://ar5iv.labs.arxiv.org/html/2307.06304/assets/moe_intro.png
\Text: Here’s a snapshot of the Uni-MoE model, illustrating its ability to handle multiple modalities using the Mixture of Experts (MoE) architecture. Let’s break down the main points of this paper.
\Headline: The Problem with Traditional Scaling
...
"""


def process_script(paper: str) -> str:
    """Generate a video script for a research paper using OpenAI's GPT-4o model.

    Parameters
    ----------
    paper : str
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
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": paper},
        ],
    )
    result = response.choices[0].message.content

    if not result:
        raise ValueError("No result returned from OpenAI.")

    return result
