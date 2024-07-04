import time
import requests
from pathlib import Path
import ffmpeg
import os
import inspect

token = os.getenv("HUGGINGFACE_WEB_TOKEN", "")
if token is None or token == "":
    raise Exception("HUGGINGFACE_WEB_TOKEN is not set")


def upload(
    video_path: Path,
    cookie_token: str,
) -> str:
    url = "https://huggingface.co/uploads"
    headers = {
        "accept": "text/plain",
        "accept-language": "en-US,en;q=0.9,fr;q=0.8",
        "content-type": "video/mp4",
        "cookie": f"token={cookie_token}",
        "origin": "https://huggingface.co",
        "x-requested-with": "XMLHttpRequest",
    }
    with video_path.open("rb") as f:
        _45MB = 45 * 1024 * 1024
        initial_size = len(f.read())
        print(f"Initial video size: {initial_size}")
        if initial_size > _45MB:
            print("Video is too large, compressing it with ffmpeg")
            compressed_video_path = video_path.with_suffix(".compressed.mp4")
            if not compressed_video_path.exists():
                input = ffmpeg.input(video_path.absolute().as_posix())
                output = ffmpeg.output(
                    input, compressed_video_path.absolute().as_posix()
                )
                ffmpeg.run(output)
            video_path = compressed_video_path
            new_size = compressed_video_path.stat().st_size
            print(f"Compressed video from {initial_size} to {new_size}")
    with video_path.open("rb") as f:
        response = requests.post(url, headers=headers, data=f)
    response.raise_for_status()
    url = response.text
    return url


def comment(
    id: str,
    token: str,
    comment: str,
) -> dict:
    url = f"https://huggingface.co/api/papers/{id}/comment"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9,fr;q=0.8",
        "content-type": "application/json",
        "cookie": f"token={token}",
        "origin": "https://huggingface.co",
    }
    data = {
        "comment": comment,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def hide(
    id: str,
    token: str,
    comment_id: str,
) -> None:
    url = f"https://huggingface.co/api/papers/{id}/comment/{comment_id}/hide"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9,fr;q=0.8",
        "content-type": "application/json",
        "cookie": f"token={token}",
        "origin": "https://huggingface.co",
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()


def check_paper_or_request(id: str):
    # https://huggingface.co/api/papers/2312.15430
    url = f"https://huggingface.co/api/papers/{id}"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9,fr;q=0.8",
        "content-type": "application/json",
        "cookie": f"token={token}",
        "origin": "https://huggingface.co",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return

    url = "https://huggingface.co/api/papers/index"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9,fr;q=0.8",
        "content-type": "application/json",
        "cookie": f"token={token}",
        "origin": "https://huggingface.co",
        "priority": "u=1, i",
        "referer": f"https://huggingface.co/papers/index?arxivId={id}",
        "sec-ch-ua": '"Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
    }
    data = {
        "arxivId": id,
    }
    print(f"Requesting {id}")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def publish_post(paper_id: str, title: str, video_path: Path):
    # Check if paper exists
    check_paper_or_request(paper_id)

    # Upload video
    video_url = upload(video_path, cookie_token=token)

    # Create post content
    content = inspect.cleandoc(f"""
        # {title}

        {video_url} 

        ## Links 🔗:
        👉 Subscribe: https://www.youtube.com/@Arxflix
        👉 Twitter: https://x.com/arxflix
        👉 LMNT (Partner): https://lmnt.com/

        
        By Arxflix
        ![9t4iCUHx_400x400-1.jpg](https://cdn-uploads.huggingface.co/production/uploads/6186ddf6a7717cb375090c01/v4S5zBurs0ouGNwYj1GEd.jpeg)
    """)

    # Publish post
    try:
        response = comment(paper_id, token, content)
    except Exception as e:
        if "Too Many Requests" in str(e):
            print("Too many requests, trying again in 1h+1min ...")
            time.sleep(60 * 61)
            response = comment(paper_id, token, content)
        else:
            raise e
    return response
