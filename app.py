from flask import Flask, request, jsonify
from pornhub_api import PornhubApi
import yt_dlp
import base64
import tempfile
import os

app = Flask(__name__)
api = PornhubApi()

# 🔍 動画検索
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "q is required"}), 400

    videos = api.search_videos.search_videos(
        query,
        ordering="mostviewed",
        period="weekly",
        tags=["black"],
    )

    return jsonify([
        {
            "id": v.video_id,
            "title": v.title
        } for v in videos
    ])


# 🎥 動画情報
@app.route("/video/<video_id>", methods=["GET"])
def video_info(video_id):
    video = api.video.get_by_id(video_id)
    return jsonify({
        "id": video.video_id,
        "title": video.title,
        "duration": getattr(video, "duration", None)
    })


# 📦 動画ファイル取得（DataURL）
@app.route("/video/<video_id>/file", methods=["GET"])
def video_file(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "video.%(ext)s")

        ydl_opts = {
            "outtmpl": output,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp4")

        with open(filename, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

    return jsonify({
        "data_url": f"data:video/mp4;base64,{data}"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
