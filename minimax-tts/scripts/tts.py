#!/usr/bin/env python3
"""MiniMax TTS - Convert text to speech and auto-play."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

BASE_URL = "https://api.minimaxi.com/v1/t2a_v2"


def load_env():
    env_paths = [
        os.path.expanduser("~/.vk-cowork/.env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.expanduser("~/.env"),
    ]
    env = {}
    for path in env_paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        k = key.strip()
                        if k not in env:
                            env[k] = value.strip().strip('"').strip("'")
    return env


def play(path):
    if sys.platform == "darwin":
        subprocess.run(["afplay", path], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["mpg123", "-q", path], check=False)
    else:
        os.startfile(path)


def tts(text, output_path=None, voice_id=None, speed=1.0, vol=1.0, pitch=0,
        emotion=None, model="speech-02-hd", no_play=False):
    env = load_env()

    api_key = os.environ.get("MINIMAX_TTS_API_KEY") or env.get("MINIMAX_TTS_API_KEY")
    group_id = os.environ.get("MINIMAX_TTS_GROUP_ID") or env.get("MINIMAX_TTS_GROUP_ID")
    default_voice = (os.environ.get("MINIMAX_TTS_VOICE_ID")
                     or env.get("MINIMAX_TTS_VOICE_ID", "Chinese (Mandarin)_Soft_Girl"))

    if not api_key:
        print("Error: MINIMAX_TTS_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not group_id:
        print("Error: MINIMAX_TTS_GROUP_ID not set", file=sys.stderr)
        sys.exit(1)

    use_tmp = output_path is None
    if use_tmp:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = tmp.name
        tmp.close()

    voice_setting = {"voice_id": voice_id or default_voice, "speed": speed, "vol": vol, "pitch": pitch}
    if emotion:
        voice_setting["emotion"] = emotion

    payload = {
        "model": model,
        "text": text,
        "voice_setting": voice_setting,
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
        "group_id": group_id,
    }

    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    status = result.get("base_resp", {})
    if status.get("status_code", 0) != 0:
        print(f"API Error: {status.get('status_msg')}", file=sys.stderr)
        sys.exit(1)

    audio_hex = result.get("data", {}).get("audio", "")
    if not audio_hex:
        print(f"Error: no audio in response\n{json.dumps(result, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "wb") as f:
        f.write(bytes.fromhex(audio_hex))

    if not no_play:
        play(output_path)

    if use_tmp:
        os.unlink(output_path)
    else:
        print(output_path)


def main():
    parser = argparse.ArgumentParser(description="MiniMax TTS — generates and plays audio")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("output", nargs="?", default=None, help="Save path (omit to play and discard)")
    parser.add_argument("--voice", help="Voice ID")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--vol", type=float, default=1.0)
    parser.add_argument("--pitch", type=int, default=0)
    parser.add_argument("--emotion", help="happy/sad/angry/fearful/disgusted/surprised/neutral")
    parser.add_argument("--model", default="speech-02-hd")
    parser.add_argument("--no-play", action="store_true", help="Save only, do not play")
    args = parser.parse_args()

    tts(
        text=args.text,
        output_path=args.output,
        voice_id=args.voice,
        speed=args.speed,
        vol=args.vol,
        pitch=args.pitch,
        emotion=args.emotion,
        model=args.model,
        no_play=args.no_play,
    )


if __name__ == "__main__":
    main()
