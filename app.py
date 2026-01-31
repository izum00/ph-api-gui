from flask import Flask, request, jsonify
import subprocess
import base64
import imageio_ffmpeg
import os
import m3u8
import tempfile
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

@app.route("/m3u8-to-video", methods=["POST"])
def m3u8_to_video():
    m3u8_url = request.json.get("m3u8_url")

    if not m3u8_url:
        return jsonify({"error": "m3u8_url is required"}), 400

    try:
        playlist = m3u8.load(m3u8_url)
    except Exception as e:
        return jsonify({"error": "failed to load m3u8", "detail": str(e)}), 400

    if not playlist.segments:
        return jsonify({"error": "no segments found"}), 400

    # ffmpeg は m3u8 を直接食えるので、
    # 解析は m3u8、変換は ffmpeg という役割分担
    cmd = [
        FFMPEG_PATH,
        "-y",
    
        "-protocol_whitelist",
        "file,http,https,tcp,tls,crypto",
    
        "-allowed_extensions", "ALL",
    
        "-i", m3u8_url,
    
        "-movflags", "frag_keyframe+empty_moov",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "aac",
    
        "-f", "mp4",
        "pipe:1"
    ]


    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if proc.returncode != 0:
        return jsonify({
            "error": "ffmpeg failed",
            "detail": proc.stderr.decode()
        }), 500

    data_url = (
        "data:video/mp4;base64," +
        base64.b64encode(proc.stdout).decode()
    )

    return jsonify({"dataUrl": data_url})


# Render 用
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
