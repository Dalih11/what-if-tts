#!/usr/bin/env python3
"""Generate TTS mp3s for the 48 winter-video clips with edge-tts.

Runs on GitHub Actions (direct internet). One consistent voice for all clips.
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
    out = os.path.join(OUTDIR, f"{clip_id}.mp3")
    last = None
    for attempt in range(1, 4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(out)
            size = os.path.getsize(out)
            if size > 1000:
                print(f"OK {clip_id} attempt={attempt} bytes={size}", flush=True)
                return True
            last = f"empty file ({size} bytes)"
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
