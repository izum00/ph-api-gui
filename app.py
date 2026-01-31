import subprocess
import ffmpeg_static
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

FFMPEG_PATH = ffmpeg_static.get_ffmpeg_exe()

@app.route("/m3u8-to-video", methods=["POST"])
def m3u8_to_video():
    m3u8_url = request.json.get("m3u8_url")

    cmd = [
        FFMPEG_PATH,
        "-i", m3u8_url,
        "-c", "copy",
        "-f", "mp4",
        "pipe:1"
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        return jsonify({"error": result.stderr.decode()}), 500

    data_url = "data:video/mp4;base64," + \
        base64.b64encode(result.stdout).decode()

    return jsonify({"dataUrl": data_url})
