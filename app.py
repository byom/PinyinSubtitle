from flask import Flask, request, jsonify, send_file
import os
import uuid
import subprocess
from pypinyin import pinyin, Style

app = Flask(__name__)

# 上传文件目录
UPLOAD_FOLDER = "./burn_service"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 字体文件路径
FONT_PATH = "./fonts/SourceHanSansSC-Bold.otf" # 确保此路径正确

def create_ass_from_srt(srt_path, ass_path):
    """
    将SRT文件转换为带拼音的ASS文件。
    """
    try:
        os.makedirs(os.path.dirname(ass_path), exist_ok=True)
        with open(srt_path, 'r', encoding='utf-8') as srt_file:
            content = srt_file.read().strip()
        if not content:
            return False
            
        segments = content.split('\n\n')
        
        ass_content = """[Script Info]
Title: Burned Subtitle
ScriptType: v4.00+
Collisions: Normal
PlayResX: 480
PlayResY: 848

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Source Han Sans SC,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,212,1
Style: Pinyin,Source Han Sans SC,30,&H00FFFF00,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,1,2,10,10,252,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        for segment in segments:
            if segment.strip():
                lines = segment.strip().split('\n')
                if len(lines) >= 3:
                    try:
                        time_range = lines[1].strip()
                        text = " ".join(lines[2:]).strip()
                        
                        if not text:
                            continue
                            
                        start, end = time_range.split(' --> ')
                        
                        start_parts = start.replace(',', '.').split(':')
                        ass_start = f"{int(start_parts[0])}:{start_parts[1].zfill(2)}:{start_parts[2][:5].ljust(5, '0')}"
                        
                        end_parts = end.replace(',', '.').split(':')
                        ass_end = f"{int(end_parts[0])}:{end_parts[1].zfill(2)}:{end_parts[2][:5].ljust(5, '0')}"

                        pinyin_list = pinyin(text, style=Style.TONE)
                        pinyin_text = "".join([item[0] + " " for item in pinyin_list]).strip()

                        ass_content += f"Dialogue: 0,{ass_start},{ass_end},Default,,0,0,0,,{text}\n"
                        ass_content += f"Dialogue: 0,{ass_start},{ass_end},Pinyin,,0,0,0,,{pinyin_text}\n"
                        
                    except Exception as e:
                        print(f"Warning: Error processing segment: {segment} -> {e}")
                        continue
        
        with open(ass_path, 'w', encoding='utf-8') as ass_file:
            ass_file.write(ass_content)
        
        if os.path.exists(ass_path) and os.path.getsize(ass_path) > 0:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error creating ASS file: {e}")
        return False

def escape_ffmpeg_filter_path(path):
    """
    为FFmpeg滤镜中的路径正确转义，特别是处理Windows路径中的冒号。
    This is ONLY for paths inside the -vf/-af filter complex.
    """
    path = path.replace('\\', '/')
    if len(path) >= 2 and path[1] == ':':
        path = path[0] + '\\:' + path[2:]
    return path

@app.route("/burn_subtitle", methods=["POST"])
def burn_subtitle():
    if "video_file" not in request.files or "subtitle_file" not in request.files:
        return jsonify({"error": "Missing video_file or subtitle_file"}), 400

    video_file = request.files["video_file"]
    subtitle_file = request.files["subtitle_file"]

    if video_file.filename == "" or subtitle_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    video_filename = os.path.basename(video_file.filename)
    subtitle_filename = os.path.basename(subtitle_file.filename)
    
    video_id = uuid.uuid4().hex
    video_path = os.path.join(UPLOAD_FOLDER, f"{video_id}_{video_filename}")
    srt_path = os.path.join(UPLOAD_FOLDER, f"{video_id}_{subtitle_filename}")
    
    video_file.save(video_path)
    subtitle_file.save(srt_path)

    ass_path = os.path.join(UPLOAD_FOLDER, f"{video_id}.ass")
    output_video_path = os.path.join(UPLOAD_FOLDER, f"burned_{video_id}_{video_filename}")

    try:
        if not create_ass_from_srt(srt_path, ass_path):
            return jsonify({"error": "Failed to convert SRT to ASS"}), 500

        abs_video_path = os.path.abspath(video_path)
        abs_ass_path = os.path.abspath(ass_path)
        abs_output_video_path = os.path.abspath(output_video_path)
        abs_font_path = os.path.abspath(FONT_PATH)
        
        output_dir = os.path.dirname(abs_output_video_path)
        os.makedirs(output_dir, exist_ok=True)

        # --- PATH HANDLING FIX ---
        # For input/output files, a simple slash conversion is safe and correct.
        video_path_ffmpeg = abs_video_path.replace('\\', '/')
        output_path_ffmpeg = abs_output_video_path.replace('\\', '/')
        
        # For paths INSIDE the filter string, we need the special colon escaping.
        ass_path_for_filter = escape_ffmpeg_filter_path(abs_ass_path)
        fonts_dir_for_filter = escape_ffmpeg_filter_path(os.path.dirname(abs_font_path))
        
        command = [
            'ffmpeg', '-y',
            '-i', video_path_ffmpeg, # Use the simple path
            '-vf', f"ass='{ass_path_for_filter}':fontsdir='{fonts_dir_for_filter}'", # Use the escaped paths
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'slow',
            '-c:a', 'copy',
            output_path_ffmpeg # Use the simple path
        ]

        print(">>> Executing FFmpeg Command:\n", " ".join(command))
        
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        
        if not os.path.exists(abs_output_video_path):
            raise Exception(f"Output video file was not created: {abs_output_video_path}")

        print(f"Video with burned subtitles created at: {output_video_path}")
        return send_file(output_video_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error Stderr: {e.stderr}")
        print(f"FFmpeg Error Stdout: {e.stdout}")
        return jsonify({"error": f"FFmpeg failed: {e.stderr}"}), 500
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Cleanup (optional, can be enabled for production)
        # for p in [video_path, srt_path, ass_path, output_video_path]:
        #     if os.path.exists(p):
        #         os.remove(p)
        pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)