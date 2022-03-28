import re
import urllib
import ffmpeg
import requests
import math
import os


def create_final_caption(
    collection_name, original_caption, user, caption_template, hashtags
):
    """
    Create a caption for a scheduled Instagram post.

    Parameters
    ----------
    collection_name : str
        The collection name in the format "<story>,<hashtags>,<caption>".
    original_caption : str
        The caption of the original post.
    user : str
        The user of the original post
    caption_template : str
        The caption template.
    hashtags : list of str
        The hashtags to use.

    Returns
    -------
    str
        The caption for a scheduled Instagram post.
    """
    story_flag, hashtag_flag, custom_caption = collection_name.split(",", 2)

    as_story = story_flag == "y"

    if as_story:
        return None

    use_hashtags = hashtag_flag == "y"

    hashtags = (
        re.findall("#[^\s]*", original_caption)
        if use_hashtags and original_caption
        else hashtags
    )
    caption = custom_caption or original_caption or ""
    final_caption = caption_template.format(
        caption=caption, hashtags=" ".join(hashtags), user=user
    )

    return final_caption


def __download_video(video_url, out_file_path):
    print(f"Downloading video ({video_url})")
    stream_info = ffmpeg.probe(video_url)
    video_duration = float(stream_info["streams"][0]["duration"])
    min_duration = 1
    loop_count = math.ceil(min_duration / video_duration) - 1

    # Download and loop video
    stream = ffmpeg.input(filename=video_url, stream_loop=loop_count)

    # Crop video if it exceeds allowed aspect ratios
    video = stream.video.filter("crop", "min(iw, ih * 16 / 9)", "min(ih, iw * 5 / 4)")

    # Check for audio and save video
    if len(stream_info["streams"]) == 1:
        ffmpeg.output(video, out_file_path).run()
    else:
        audio = stream.audio
        ffmpeg.output(video, audio, out_file_path).run()
    print(f"Successfully downloaded video ({os.path.abspath(out_file_path)})")


def __download_photo(photo_url, out_file_path):
    print(f"Downloading photo ({photo_url})")
    image_data = requests.get(photo_url).content
    with open(out_file_path, "wb") as file:
        file.write(image_data)
    print(f"Successfully downloaded photo ({os.path.abspath(out_file_path)})")


def download_media(media_urls, out_dir_path):
    """
    Download media from a list URLs.

    Parameters
    ----------
    media_urls : list of str
        The media URLs from which to download media.
    out_dir_path : str
        The directory path to download media to.
    """
    for i, media_url in enumerate(media_urls):
        media_path = urllib.parse.urlparse(media_url).path
        media_extension = os.path.splitext(media_path)[1]

        if media_extension == ".mp4":
            out_file_path = os.path.join(out_dir_path, f"{i}.mp4")
            __download_video(media_url, out_file_path)
        else:
            out_file_path = os.path.join(out_dir_path, f"{i}.jpg")
            __download_photo(media_url, out_file_path)
