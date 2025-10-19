from litestar import Litestar, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar import Response
from typing import Dict, Any, List
import sounddevice as sd
import queue, threading, json, os
from vosk import Model, KaldiRecognizer
import soundfile as sf
from transformers import pipeline, AutoTokenizer
from pathlib import Path
import logging
from datetime import datetime

# -------------------- ЛОГИРОВАНИЕ --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- НАСТРОЙКА --------------------
q = queue.Queue()
stop_mic = False
mic_results: List[str] = []

MODEL_PATH = r"models/vosk-model-small-ru-0.22"
PUNCT_MODEL_PATH = r"models/RUPunct_big"

print("🔄 Загрузка моделей...")
try:
    vosk_model = Model(MODEL_PATH)
    tk = AutoTokenizer.from_pretrained(PUNCT_MODEL_PATH, strip_accents=False, add_prefix_space=True)
    classifier = pipeline("ner", model=PUNCT_MODEL_PATH, tokenizer=tk, aggregation_strategy="first", device=-1)
    print("✅ Модели загружены!")
except Exception as e:
    print(f"❌ Ошибка загрузки моделей: {e}")
    raise


def process_token(token, label):
    mapping = {
        "LOWER_O": token, "LOWER_PERIOD": token + ".", "LOWER_COMMA": token + ",",
        "LOWER_QUESTION": token + "?", "LOWER_TIRE": token + "—", "LOWER_DVOETOCHIE": token + ":",
        "LOWER_VOSKL": token + "!", "LOWER_PERIODCOMMA": token + ";", "LOWER_DEFIS": token + "-",
        "LOWER_MNOGOTOCHIE": token + "...",
        "UPPER_O": token.capitalize(), "UPPER_PERIOD": token.capitalize() + ".",
        "UPPER_COMMA": token.capitalize() + ",", "UPPER_QUESTION": token.capitalize() + "?",
        "UPPER_TIRE": token.capitalize() + " —", "UPPER_DVOETOCHIE": token.capitalize() + ":",
        "UPPER_VOSKL": token.capitalize() + "!", "UPPER_PERIODCOMMA": token.capitalize() + ";",
        "UPPER_DEFIS": token.capitalize() + "-", "UPPER_MNOGOTOCHIE": token.capitalize() + "...",
        "UPPER_TOTAL_O": token.upper(), "UPPER_TOTAL_PERIOD": token.upper() + ".",
        "UPPER_TOTAL_COMMA": token.upper() + ",", "UPPER_TOTAL_QUESTION": token.upper() + "?",
        "UPPER_TOTAL_TIRE": token.upper() + " —", "UPPER_TOTAL_DVOETOCHIE": token.upper() + ":",
        "UPPER_TOTAL_VOSKL": token.upper() + "!", "UPPER_TOTAL_PERIODCOMMA": token.upper() + ";",
        "UPPER_TOTAL_DEFIS": token.upper() + "-", "UPPER_TOTAL_MNOGOTOCHIE": token.upper() + "...",
    }
    return mapping.get(label, token)


def split_text(text, chunk_size=200):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])


def restore_punctuation(raw_text: str) -> str:
    if not raw_text: return ""
    try:
        output = ""
        for chunk in split_text(raw_text):
            preds = classifier(chunk)
            if not preds: continue
            for item in preds:
                output += " " + process_token(item["word"].strip(), item["entity_group"])
        return output.strip()
    except Exception as e:
        print(f"Ошибка пунктуации: {e}")
        return raw_text


def transcribe_file(filepath: Path) -> str:
    try:
        data, samplerate = sf.read(filepath, dtype="int16")
        rec = KaldiRecognizer(vosk_model, samplerate)
        result = []
        for chunk in range(0, len(data), 16000):
            if chunk + 16000 <= len(data):
                if rec.AcceptWaveform(data[chunk:chunk + 16000].tobytes()):
                    res = json.loads(rec.Result())
                    if res.get("text"): result.append(res["text"])
        res = json.loads(rec.FinalResult())
        if res.get("text"): result.append(res["text"])
        raw_text = " ".join(result)
        return restore_punctuation(raw_text)
    except Exception as e:
        print(f"❌ Ошибка транскрипции файла: {e}")
        return ""


# -------------------- ROUTES --------------------
@get("/")
async def index() -> Response:
    try:
        with open("app/web/templates/index.html", "r", encoding="utf-8") as f:  # ← НОВЫЙ ПУТЬ!
            html = f.read()
        return Response(content=html, media_type="text/html")
    except FileNotFoundError:
        return Response(content="<h1>❌ Не найдена app/web/templates/index.html</h1>", media_type="text/html")


@post("/upload")
async def upload_audio(data: Dict[str, UploadFile] = Body(media_type=RequestEncodingType.MULTI_PART)) -> Dict[str, Any]:
    try:
        file = data["file"]
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        filepath = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        print(f"📁 Файл сохранен: {filepath}")
        text = transcribe_file(filepath)
        return {"text": text, "status": "success", "filename": file.filename}
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return {"text": "", "status": "error", "message": str(e)}


def mic_worker(samplerate: int, device: int, callback):
    global stop_mic
    rec = KaldiRecognizer(vosk_model, samplerate)

    def sd_callback(indata, frames, time, status):
        if status: print("⚠", status)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=samplerate, blocksize=16000, device=device,
                           dtype="int16", channels=1, callback=sd_callback):
        while not stop_mic:
            try:
                data = q.get(timeout=0.1)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get("text"):
                        restored = restore_punctuation(result["text"])
                        callback(restored)
            except queue.Empty:
                continue


@post("/start_mic")
async def start_mic() -> Dict[str, Any]:
    global stop_mic
    try:
        stop_mic = False
        mic_results.clear()

        devices = sd.query_devices()
        input_device = next((i for i, d in enumerate(devices) if d["max_input_channels"] > 0), None)
        if input_device is None:
            return {"status": "error", "message": "Нет доступных микрофонов"}

        samplerate = int(sd.query_devices(input_device, "input")["default_samplerate"])
        print(f"🎤 Микрофон запущен: устройство {input_device}, {samplerate}Hz")

        def send_update(text):
            mic_results.append(text)
            print(f"🎤 {text}")

        threading.Thread(target=mic_worker, args=(samplerate, input_device, send_update), daemon=True).start()
        return {"status": "mic started", "device": input_device, "samplerate": samplerate}
    except Exception as e:
        print(f"❌ Ошибка запуска микрофона: {e}")
        return {"status": "error", "message": str(e)}


@post("/stop_mic")
async def stop_mic_recording() -> Dict[str, Any]:
    global stop_mic
    stop_mic = True
    print("🛑 Микрофон остановлен")
    return {"status": "mic stopped"}


@get("/get_mic")
async def get_mic() -> Dict[str, Any]:
    full_text = " ".join(mic_results)
    return {"text": full_text, "segments": len(mic_results)}


@get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mic_active": not stop_mic,
        "mic_segments": len(mic_results)
    }


# -------------------- APP (Windows 2.18.0 FIX) --------------------
app = Litestar(
    route_handlers=[
        index, upload_audio, start_mic,
        stop_mic_recording, get_mic, health_check
    ],
    debug=True
    # ✅ УБРАНЫ: title, version, openapi_url
)

if __name__ == "__main__":
    import uvicorn

    print("🚀 Сервер запускается на http://localhost:8000")
    print("📱 Мобильный: http://ВАШ_IP:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)  # ✅ БЕЗ reload