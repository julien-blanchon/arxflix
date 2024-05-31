import urllib.request
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
from typing import Any


def fetch_html(url: str) -> str:
    """
    Fetch HTML content from a given URL.

    Args:
        url (str): The URL to fetch HTML from.

    Returns:
        str: The HTML content as a string.
    """
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")


def convert_to_markdown(soup: BeautifulSoup, **options: Any) -> str:
    """
    Convert a BeautifulSoup object to Markdown.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to convert.
        **options: Additional options for MarkdownConverter.

    Returns:
        str: The converted Markdown string.
    """
    return MarkdownConverter(**options).convert_soup(soup)


def replace_math_tags(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Replace math tags in the BeautifulSoup object with corresponding LaTeX strings.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing math tags.

    Returns:
        BeautifulSoup: The modified BeautifulSoup object.
    """
    math_tags = soup.findAll("math")
    for math_tag in math_tags:
        display = math_tag.attrs.get("display")
        latex = math_tag.attrs.get("alttext")

        if not latex:
            continue

        if display == "inline":
            latex = f"${latex}$"
        elif display == "block":
            latex = f"$$ {latex} $$"
        else:
            continue

        span_tag = soup.new_tag("span")
        span_tag.string = latex
        math_tag.replace_with(span_tag)
    return soup


def remove_authors_section(article: BeautifulSoup) -> BeautifulSoup:
    """
    Remove the authors section from the article.

    Args:
        article (BeautifulSoup): The BeautifulSoup object containing the article.
    """
    authors_div = article.find("div", class_="ltx_authors")
    if authors_div:
        authors_div.decompose()  # type: ignore
    return article


def remove_bibliography(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Remove the authors section from the soup.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the soup.
    """
    bibliography = soup.find("section", class_="ltx_bibliography")
    if bibliography:
        bibliography.decompose()  # type: ignore
    return soup


def remove_appendix(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Remove the authors section from the soup.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the soup.
    """
    while soup.find("section", class_="ltx_appendix"):
        soup.find("section", class_="ltx_appendix").decompose()  # type: ignore
    return soup


def remove_ltx_para(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Remove the authors section from the soup.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the soup.
    """
    ltx_para = soup.find("div", class_="ltx_para")
    if ltx_para:
        ltx_para.decompose()  # type: ignore
    return soup


def strip_attributes(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Strip all attributes from tags except 'src'.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to process.

    Returns:
        BeautifulSoup: The modified BeautifulSoup object.
    """
    for tag in soup.find_all(True):
        tag.attrs = {key: value for key, value in tag.attrs.items() if key == "src"}
    return soup


def process_article(url: str) -> str:
    """Process an article from a given URL and save it as a markdown file.
    You need to give an `https://ar5iv.org/html` or `https://arxiv.org/html` URL.

    Args:
        url (str): The URL of the article.

    Returns:
        str: The processed article as a markdown string.
    """
    html_content = fetch_html(url)
    soup = BeautifulSoup(html_content, "html.parser")

    replace_math_tags(soup)
    remove_bibliography(soup)
    remove_ltx_para(soup)
    remove_appendix(soup)

    article = soup.find("article")
    if not article:
        raise ValueError("No article found in the HTML content.")

    remove_authors_section(article)  # type: ignore
    strip_attributes(article)  # type: ignore

    markdown_article = convert_to_markdown(article, wrap_width=True, strip=["button"])  # type: ignore
    markdown_article = markdown_article.replace("\n\n\n", "\n\n").replace(
        "\n\n\n", "\n\n"
    )
    return markdown_article
