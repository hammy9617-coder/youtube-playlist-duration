from flask import Flask, request, jsonify, send_from_directory
import yt_dlp, re, threading, time

app = Flask(__name__, static_folder="static")
cache = {}

def parse_playlist(url):
    m = re.search(r'(?:[?&]list=)([A-Za-z0-9_-]+)', url)
    return m.group(1) if m else None

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not parse_playlist(url):
        return jsonify(error="ไม่พบ Playlist ID ในลิงก์นี้"), 400

    key = parse_playlist(url)
    if key in cache and time.time() - cache[key]["ts"] < 600:
        return jsonify(cache[key]["data"])

    opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "skip_download": True,
        "playlistend": None,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        entries = [e for e in (info.get("entries") or []) if e]
        durations = [int(e.get("duration") or 0) for e in entries]
        total = sum(durations)
        result = {
            "title": info.get("title") or "Playlist",
            "count": len(entries),
            "known": sum(1 for x in durations if x > 0),
            "seconds": total
        }
        cache[key] = {"ts": time.time(), "data": result}
        return jsonify(result)
    except Exception as e:
        return jsonify(error="ดึงข้อมูลไม่สำเร็จ: " + str(e)[:300]), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
