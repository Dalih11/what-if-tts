#!/usr/bin/env python3
"""Generate TTS mp3s + word timings with edge-tts.

Runs on GitHub Actions (direct internet). One consistent voice for all clips.
Reads clips.json, writes out/<id>.mp3 and out/<id>.words.json (word boundary
offsets in seconds, for kinetic captions).
"""
import asyncio
import json
import os
import sys

import edge_tts

VOICE = "en-US-BrianNeural"
RATE = "+0%"
OUTDIR = "out"


async def one(clip_id, text):
    out_mp3 = os.path.join(OUTDIR, f"{clip_id}.mp3")
    out_words = os.path.join(OUTDIR, f"{clip_id}.words.json")
    last = None
    for attempt in range(1, 4):
        try:
            audio = bytearray()
            words = []
            async for chunk in edge_tts.Communicate(text, VOICE, rate=RATE).stream():
                if chunk["type"] == "audio":
                    audio += chunk["data"]
                elif chunk["type"] == "WordBoundary":
                    words.append({
                        "word": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,
                        "duration": chunk["duration"] / 10_000_000,
                    })
            if len(audio) > 1000:
                with open(out_mp3, "wb") as f:
                    f.write(audio)
                with open(out_words, "w", encoding="utf-8") as f:
                    json.dump({"id": clip_id, "text": text, "words": words}, f)
                print(f"OK {clip_id} attempt={attempt} bytes={len(audio)} words={len(words)}", flush=True)
                return True
            last = f"empty audio ({len(audio)} bytes)"
        except Exception as e:  # noqa: BLE001
            last = str(e)[:200]
            print(f"{clip_id} attempt {attempt}/3 failed: {last}", flush=True)
        await asyncio.sleep(5 * attempt)
    print(f"FAILED {clip_id}: {last}", flush=True)
    return False


async def main():
    os.makedirs(OUTDIR, exist_ok=True)
    clips = json.load(open("clips.json", encoding="utf-8"))["clips"]
    failed = []
    for c in clips:
        ok = await one(c["id"], c["text"])
        if not ok:
            failed.append(c["id"])
    print(f"done: {len(clips) - len(failed)}/{len(clips)} clips")
    if failed:
        sys.exit(f"failed clips: {','.join(failed)}")


asyncio.run(main())
