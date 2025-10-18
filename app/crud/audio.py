from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import AudioFile
from app.schemas import AudioFileSchema
import msgspec

async def get_audio_json(session: AsyncSession, file_id: int) -> bytes:
    result = await session.execute(select(AudioFile).where(AudioFile.id == file_id))
    audio = result.scalar_one_or_none()
    if not audio:
        return msgspec.json.encode({"error": "Not found"})
    schema = AudioFileSchema(
        id=audio.id,
        url=audio.url,
        status=audio.status,
        transcription=audio.transcription,
    )
    return msgspec.json.encode(schema)
