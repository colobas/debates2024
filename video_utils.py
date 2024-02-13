import subprocess
from pathlib import Path
import json
from urllib.parse import quote
from tqdm import trange


def set_public_permission(file_id, service):
    anyone_permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(
        fileId=file_id,
        body=anyone_permission,
    ).execute()


def direct_link(file_id):
    video_url = f"https://drive.google.com/uc?id={file_id}"

    #return "https://api.allorigins.win/raw?url=" + quote(video_url, safe="")
    #return "https://corsproxy.io/?" + quote(video_url, safe="")
    return "https://worker-little-base-2714.mail-2e4.workers.dev/?" + quote(video_url, safe="")


def get_segment_file_ids(slug):
    # get segment file ids: rclone lsjson remoteName:targetFolder --files-only | jq '.[] | {name, id}'
    cmd = [
        "rclone", "lsjson",
        f"debates:debates2024/{slug}",
        "--files-only",
    ]

    result = subprocess.run(cmd, capture_output=True, check=True)

    cmd = [
        "jq", ".[] | {Name, ID}",
    ]
    result = subprocess.run(cmd, input=result.stdout, capture_output=True, check=True)

    file_ids = {}
    for d in result.stdout.decode("utf-8").split("}\n"):
        try:
            d = json.loads(d+"}")
            file_ids[d["Name"].strip()] = d["ID"].strip()
        except:
            pass

    return file_ids


def set_folder_permissions(slug, service):
    folder_name = f"debates2024/{slug}"

    # get folder id
    result = service.files().list(q=f"name='{folder_name}'").execute()
    folder_id = result["files"][0]["id"]

    # set folder permissions
    anyone_permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(
        fileId=folder_id,
        body=anyone_permission,
    ).execute()

def get_segment_duration(segment_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        str(segment_path),
    ]
    result = subprocess.run(cmd, capture_output=True, check=True)
    return float(result.stdout.decode("utf-8"))


def upload_to_gdrive(root_path, slug, service):
    cmd = [
        "rclone", "mkdir", f"debates:debates2024/{slug}",
    ]
    subprocess.run(cmd, check=True)

    # copy ts segments to gdrive
    cmd = [
        "rclone", "copy", "--check-first", "--progress", str(root_path),
        "--include", f"{slug}_segment_*.ts",
        "--ignore-existing",
        f"debates:debates2024/{slug}",
    ]
    subprocess.run(cmd, check=True)

    # get segment file ids
    file_ids = get_segment_file_ids(slug)

    # make m3u8
    with open(f"{root_path}/{slug}.m3u8", "w") as f:
        all_segments = list(root_path.glob(f"{slug}_segment_*.ts"))
        n_segments = len(all_segments)
        n_digits = 1 if n_segments < 10 else 2 if n_segments < 100 else 3

        f.write(f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:20\n#EXT-X-MEDIA-SEQUENCE:0\n")

        for i in trange(n_segments, desc="Creating m3u8..."):
            segment_path = f"{slug}_segment_{i:0{n_digits}d}.ts"
            file_id = file_ids[segment_path]
            #set_public_permission(file_id, service)

            # get duration
            duration = get_segment_duration(root_path / segment_path)

            f.write(f"#EXTINF:{duration},\n")
            f.write(direct_link(file_id) + "\n")
        f.write("#EXT-X-ENDLIST\n")

    return
