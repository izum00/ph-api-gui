from flask import Flask, request, jsonify
import subprocess
import base64
import imageio_ffmpeg
import os

app = Flask(__name__)
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

@app.route("/m3u8-to-video", methods=["POST"])
def m3u8_to_video():
    m3u8_url = request.json.get("m3u8_url")

    if not m3u8_url:
        return jsonify({"error": "m3u8_url is required"}), 400

    cmd = [
        FFMPEG_PATH,
        "-loglevel", "error",
        "-i", m3u8_url,
        "-c", "copy",
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


# ★ これが無いと Render では即死します
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
