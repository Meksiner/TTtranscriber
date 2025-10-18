from app.schemas import AudioFileSchema
import msgspec

audio = AudioFileSchema(id=1, url="https://example.com/audio.mp3")

# сериализация в JSON (bytes)
data = msgspec.json.encode(audio)
print(data)

# десериализация обратно
decoded = msgspec.json.decode(data, type=AudioFileSchema)
print(decoded)

import json, msgspec, time
from app.schemas import AudioFileSchema

data = {"id": 1, "url": "a.mp3", "status": "queued", "transcription": None}

# JSON stdlib
t0 = time.perf_counter()
for _ in range(100_000):
    json.dumps(data)
print("stdlib:", time.perf_counter() - t0)

# msgspec
struct = AudioFileSchema(**data)
t1 = time.perf_counter()
for _ in range(100_000):
    msgspec.json.encode(struct)
print("msgspec:", time.perf_counter() - t1)
