import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)  # completely disable Vosk/Kaldi logging

MODEL_PATH = "vosk-model-small-de-zamia-0.3"  # Change if needed

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
