import time
import json
import sys
import asyncio
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_chromium_fake_audio_file():
    wav_path = r"c:\Users\joyce\voice-guard\data\real\asvspoof_real_02.wav"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    print(f"Launching Chrome from {chrome_path} with --use-file-for-fake-audio-capture={wav_path}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_path,
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                f"--use-file-for-fake-audio-capture={wav_path}",
                "--no-sandbox"
            ]
        )
        context = browser.new_context()
        page = context.new_page()

        page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}", flush=True))

        page.goto("http://localhost:5173/")
        page.wait_for_timeout(2000)

        # Confirm initial state
        initial_text = page.locator("div:has-text('[REAL-TIME RISK METER]')").first.inner_text()
        print("Initial Risk Meter text:\n", initial_text[:150], flush=True)

        # Click [START STREAM]
        start_btn = page.locator("button:has-text('[START STREAM]')")
        print("\nClicking [START STREAM]...", flush=True)
        start_btn.click()

        # Monitor updates over 10 seconds
        for i in range(5):
            page.wait_for_timeout(2000)
            score_text = page.locator("div:has-text('[REAL-TIME RISK METER]')").first.inner_text()
            print(f"\n--- Stream Update {i+1} (at {(i+1)*2}s) ---", flush=True)
            lines = [l.strip() for l in score_text.split("\n") if l.strip()]
            print(" | ".join(lines[:8]), flush=True)

        # Stop stream
        stop_btn = page.locator("button:has-text('[STOP STREAM]')")
        print("\nClicking [STOP STREAM]...", flush=True)
        stop_btn.click()
        page.wait_for_timeout(1000)

        browser.close()

if __name__ == "__main__":
    test_chromium_fake_audio_file()
