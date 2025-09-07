import requests

# 服务端地址
URL = "http://127.0.0.1:5050/burn_subtitle"

# 本地文件路径
VIDEO_FILE = "./test/test_video.mp4"
SUBTITLE_FILE = "./test/test_subs.srt"

print("Uploading files to the server...")

try:
    with open(VIDEO_FILE, 'rb') as video, open(SUBTITLE_FILE, 'rb') as subtitle:
        files = {
            'video_file': (VIDEO_FILE, video, 'video/mp4'),
            'subtitle_file': (SUBTITLE_FILE, subtitle, 'application/x-subrip')
        }
        
        response = requests.post(URL, files=files)

    if response.status_code == 200:
        # 保存返回的视频文件
        output_filename = "output_video_with_subs.mp4"
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f"Success! Burned video saved as {output_filename}")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

except FileNotFoundError as e:
    print(f"Error: Make sure {e.filename} exists in the current directory.")
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")