import msgspec

class AudioFileSchema(msgspec.Struct):
    id: int
    url: str
    status: str = "queued"
    transcription: str | None = None
