import os
import dotenv
import argparse
import subprocess
import logging
import hashlib
from pathlib import Path

import yaml
import json
import re

import bs4
import requests
import webvtt

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from video_utils import upload_to_gdrive

def convert_to_seconds(time):
    """
    Convert a time in the format 00:00:01.216 to seconds
    """

    h, m, s = time.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def webvtt_to_json(vtt_path, output_path):
    # adapted from: https://github.com/simonw/webvtt-to-json/blob/main/webvtt_to_json/cli.py
    with open(vtt_path, "r") as vtt_file:
        captions = webvtt.read_buffer(vtt_file)
    dicts = [{"start": c.start, "end": c.end, "lines": c.lines} for c in captions]
    dicts = []
    prev_line = None
    for c in captions:
        if any("<c>" in l for l in c.lines):
            continue
        # Collect lines that are not dupes
        not_dupe_lines = []
        for line in c.lines:
            if not line.strip():
                continue
            if line != prev_line:
                not_dupe_lines.append(line)
            prev_line = line
        if not_dupe_lines:
            dicts.append({"start": c.start, "end": c.end, "lines": not_dupe_lines})

    for d in dicts:
        line = "\n".join(d.pop("lines"))
        d["speaker"], d["text"] = [_.strip() for _ in line.split(":", 1)]
        d["time"] = convert_to_seconds(d.pop('start'))
        d.pop('end')

    with open(output_path, "w") as output:
        json.dump(dicts, output, indent=4, ensure_ascii=False)


def find_m3u8_and_thumbnail(url):
    """
    Find the m3u8 link and thumbnail from a given debate URL. This will depend on
    the specific website where the debates are hosted
    """

    if "sicnoticias.pt" in url:
        # sic noticias
        # the m3u8 url and the thumbnail url are in a script tag of type "application/ld+json"
        bs = bs4.BeautifulSoup(requests.get(url).text, "html.parser")
        scripts = bs.find_all("script", type="application/ld+json")
        for script in scripts:
            # read json
            data = json.loads(script.string)
            if data["@type"] == "VideoObject":
                return data["contentUrl"], data["thumbnailUrl"]
    elif "rtp.pt" in url:
        # https://www.rtp.pt/play/{SERIES}/e746061/debates-legislativas-2024
        # m3u8: https://streaming-vod.rtp.pt/hls/nas2.share,/h264/512x384/p12900/p12900_1_2024020515461.mp4,.urlset/master.m3u8
        # thumbnail: https://cdn-images.rtp.pt/multimedia/screenshots/p12900/p12900_1_2024020515461.jpg?q=100&format=pjpg&auto=webp&v=3&w=400
        #
        # we can find the necessary reference from a string like:
        # "seekBarThumbnailsLoc: '//cdn-images.rtp.pt/multimedia/screenshots/p12900/preview/{SERIES}_1_2024020515461_preview.vtt',"

        series = url.split("/")[-3]

        text = requests.get(url).text
        pat = rf"seekBarThumbnailsLoc: '.*preview/({series}.*)\.vtt',"
        ref = re.findall(pat, text)[0].split("_")[:-1] # it ends in _preview
        ref = "_".join(ref)

        m3u8_url = f"https://streaming-vod.rtp.pt/hls/nas2.share,/h264/512x384/{series}/{ref}.mp4,.urlset/master.m3u8"
        thumbnail_url = f"https://cdn-images.rtp.pt/multimedia/screenshots/{series}/{ref}.jpg?q=100&format=pjpg&auto=webp&v=3&w=400"
        return m3u8_url, thumbnail_url

    return None, None


def get_audio_and_video(url, audio_path, headers=None, gdrive_service=None):
    """
    Use ffmpeg to download the audio and video from a given m3u8 link
    """

    Path(audio_path).parent.mkdir(exist_ok=True, parents=True)

    m3u8_path = audio_path.with_suffix(".m3u8")
    m3u8_orig_path = audio_path.with_suffix(".m3u8.orig")

    if not m3u8_path.exists():
        mp4_path = audio_path.with_suffix(".mp4")

        # download video
        if not mp4_path.exists():
            if headers is not None:
                headers = "\r\n".join([f"{k}: {v}" for k,v in headers.items()]) + "\r\n"
                cmd = ["ffmpeg", "-headers", headers, "-i", url, "-c", "copy", mp4_path]
            else:
                cmd = ["ffmpeg", "-i", url, "-c", "copy", mp4_path]
            subprocess.run(cmd)

        if not m3u8_orig_path.exists():
            # create hls
            options = [
                "-hls_time", "10", # segment duration
                "-hls_list_size", "0", # list all segments
                "-hls_segment_filename", f"{m3u8_path.with_suffix('')}_segment_%03d.ts",
                "-f", "hls",
            ]

            cmd = ["ffmpeg", "-i", mp4_path, *options, str(m3u8_orig_path)]
            subprocess.run(cmd)

            # upload to gdrive using rclone

        if not audio_path.exists():
            # extract audio
            options = [
                "-vn", # Disables video recording
                "-acodec", "libmp3lame", # Specifies MP3 encoding
                "-q:a", "0", # High quality audio
               ]

            cmd = ["ffmpeg", "-i", mp4_path, *options, audio_path]
            subprocess.run(cmd)

        # upload the video to youtube
        upload_to_gdrive(audio_path.parent, audio_path.stem, gdrive_service)

    return f"debates/media/{audio_path.stem}.m3u8"


def slugify(title):
    """
    Turn a title into a slug
    """

    return title.lower().replace(" ", "-")


def transcribe_audio(audio_path, output_root):
    """
    use whisperx to transcribe the audio
    """

    name = audio_path.stem

    if not (output_root / f"transcriptions/{name}.json").exists():
        Path(f"{output_root}/transcriptions").mkdir(exist_ok=True, parents=True)

        cmd = [
            "whisperx",
            "--hf_token",
            os.environ["HF_TOKEN"],
            "--model",
            "large-v2",
            "--language",
            "pt",
            "--diarize",
            "--min_speakers",
            "2",
            "--max_speakers",
            "4",
            "--compute_type",
            "int8",
            "--output_dir",
            f"{output_root}/transcriptions",
            "--print_progress",
            "True",
            audio_path,
           ]

        subprocess.run(cmd)

        # keep only the .vtt file
        for f in Path(f"{output_root}/transcriptions").glob(f"{name}.*"):
            if f.suffix not in [".vtt"]:
                f.unlink()

        # convert the vtt to json
        webvtt_to_json(f"{output_root}/transcriptions/{name}.vtt", f"{output_root}/transcriptions/{name}.json")

        # remove the vtt
        (output_root / f"transcriptions/{name}.vtt").unlink()


def process_debate(*, title, url, output_root, gdrive_service, skip_transcription=False, skip_upload=False):
    """
    Process a debate from the input data
    """

    m3u8_url, thumbnail_url = find_m3u8_and_thumbnail(url)
    if m3u8_url is None or thumbnail_url is None:
        logging.warning(f"Could not find m3u8 or thumbnail for {url}")
        return

    slug = slugify(title)
    audio_path = output_root / f"media/{slug}.mp3"

    if "rtp.pt" in url:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.rtp.pt/",
            "Origin": "https://www.rtp.pt",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers"
        }
    else:
        headers = None

    if not skip_upload:
        get_audio_and_video(m3u8_url, audio_path, headers=headers, gdrive_service=gdrive_service)
        out = {
            "slug": slug,
            "title": title,
            "original_url": url,
        }

        with open(output_root / f"{slug}.json", "w") as f:
            json.dump(out, f, indent=4)

    if not skip_transcription:
        transcribe_audio(audio_path, output_root)

    return {"title": title, "thumbnail": thumbnail_url, "slug": slug}


def main(args):
    input_path = Path(args.input)
    output_root = Path(args.output_root)
    output_root.mkdir(exist_ok=True, parents=True)

    CLIENT_SECRETS_FILE = os.environ["CLIENT_SECRETS_FILE"]
    creds = Credentials.from_authorized_user_file(CLIENT_SECRETS_FILE)
    gdrive_service = build('drive', 'v3', credentials=creds)

    with open(input_path, "r") as f:
        data = yaml.safe_load(f)

    master_json = []
    for debate in data:
        output_path = output_root / f"{debate}.json"

        if output_path.exists() and not args.force:
            continue

        summary = process_debate(**debate, output_root=output_root, skip_transcription=args.skip_transcription, gdrive_service=gdrive_service, skip_upload=args.skip_upload)
        master_json.append(summary)

    with open(args.output_master_json, "w") as f:
        json.dump(master_json, f, indent=4)


if __name__ == "__main__":
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="debates.yaml")
    parser.add_argument("--output_root", type=str, default="public/debates")
    parser.add_argument("--output-master-json", type=str, default="src/debates.json")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-transcription", action="store_true")
    parser.add_argument("--skip-upload", action="store_true")
    args = parser.parse_args()
    main(args)
