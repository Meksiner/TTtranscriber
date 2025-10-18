from litestar import Litestar
from app.web.routes import upload_audio, start_mic, stop_mic_recording, get_mic, index

app = Litestar(route_handlers=[
    upload_audio,
    start_mic,
    stop_mic_recording,
    get_mic,
    index
])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
