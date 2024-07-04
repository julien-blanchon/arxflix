from openai import OpenAI
import requests
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
- Avoid markdown listing (1., 2., or - dash) at all cost. Use full sentences that are easy to understand in spoken language.
- For \Equation: Don't use $ or \[, the latex context is automatically detected.
- For \Equation: Always write everything in the same line, multiple lines will generate an error. Don't make table.
- You should always follow the syntax, don't start a line without a slash (\) command. Don't hallucinate figures.

Here an example what you need to produce:
\Headline: Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts
\Text: Welcome back to Arxflix! Today, we’re diving into an exciting new paper titled "Uni-MoE: Scaling Unified Multimodal LLMs with Mixture of Experts". This research addresses the challenge of efficiently scaling multimodal large language models (MLLMs) to handle a variety of data types like text, images, audio, and video.
\Figure: https://...
\Text: Here’s a snapshot of the Uni-MoE model, illustrating its ability to handle multiple modalities using the Mixture of Experts (MoE) architecture. Let’s break down the main points of this paper.
\Headline: The Problem with Traditional Scaling
...
"""
SYSTEM_PROMPT_INTRO = r"""
You're a researcher that summerize research contain on Youtube.
Now you need a name and a figure for the video thumbnail.
The title should be appealing, yet not to far from the original paper title.
You can use emojis for the title but keep it professional.

For the figure, provide the link with https:// and the .png extension.
Your output follow this format:
The Selected Title
The Selected Figure Link

Your ouput will have just two lines, without description.
The first \Headline of the reference is a very good starting point for the title.
Here is the script you wrote, as a reference:
"""


def correct_result_link(script: str, url: str) -> str:
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

    split_script = script.split("\n")

    for line_idx, line in enumerate(split_script):
        if r"\Figure: " in line and not line.startswith("https"):
            tmp_line = line.replace(r"\Figure: ", "")

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
                    split_script[line_idx] = r"\Figure: " + figure_url
                else:
                    # Remove "ar5iv.labs." and try again
                    figure_url = figure_url.replace("ar5iv.labs.", "")
                    response = requests.head(figure_url)
                    if (
                        response.status_code == 200
                        and "image/png" in response.headers.get("Content-Type", "")
                    ):
                        split_script[line_idx] = r"\Figure: " + figure_url
            except requests.exceptions.RequestException:
                # If the request fails, leave the link as is (or handle the error as you prefer)
                pass

    return "\n".join(split_script)


def process_script(paper: str, url: str) -> tuple[str, str]:
    """Generate a video script for a research paper using OpenAI's GPT-4o model.

    Parameters
    ----------
    paper : str
        A research paper in markdown format. (For the moment, it's HTML)
    url : str
        The url of the paper

    Returns
    -------
    str
        The generated video script.
    str
        The generated video script intro.

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

    # response_intro = openai_client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": SYSTEM_PROMPT_INTRO},
    #         {"role": "user", "content": result},
    #     ],
    # )
    # result_intro = response_intro.choices[0].message.content

    # if not result_intro:
    #     raise ValueError("No intro returned from OpenAI.")

    # Other way to get the intro
    result_lines = result.split("\n")
    # first \Headline
    first_headline = result_lines.index(
        [line for line in result_lines if line.startswith(r"\Headline")][0]
    )
    first_figure = result_lines.index(
        [line for line in result_lines if line.startswith(r"\Figure")][0]
    )
    first_headline = (
        result_lines[first_headline]
        .replace(r"\Headline: ", "")
        .strip()
        .replace("\n", "")
    )
    first_figure = (
        result_lines[first_figure].replace(r"\Figure: ", "").strip().replace("\n", "")
    )
    result_intro = first_headline + "\n" + first_figure

    # script = correct_result_link(result, url)
    script = result
    return script, result_intro
