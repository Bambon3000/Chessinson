import os
import sys

# 🔇 HARD silence ALSA / PortAudio (C-level stderr)
devnull = os.open(os.devnull, os.O_WRONLY)
saved_stderr_fd = os.dup(2)
os.dup2(devnull, 2)
os.close(devnull)

import json
import pyaudio
from vosk import Model, KaldiRecognizer, SetLogLevel

# Restore stderr for normal Python errors
os.dup2(saved_stderr_fd, 2)
os.close(saved_stderr_fd)

# 🔇 Silence Vosk / Kaldi
SetLogLevel(-1)

MODEL_PATH = "vosk-model-small-de-zamia-0.3" # Change if needed

def listen():
    print("Loading Vosk model...")
    model = Model(MODEL_PATH)

    allowed = [
        "springer", "läufer", "turm", "dame", "könig", "bauer",
        "a", "b", "c", "d", "e", "f", "g", "h",
        "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht",
        "von", "nach", "auf", "zu"
    ]

    recognizer = KaldiRecognizer(model, 16000, json.dumps(allowed, ensure_ascii=False))
    recognizer.SetWords(True)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192
    )
    stream.start_stream()

    print("🎤 Please say your move...")

    try:
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    print("• Recognized:", text)
                    return text
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__listen__":
    listen()
