from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer


class Base(DeclarativeBase):
    pass


class AudioFile(Base):
    __tablename__ = "audio_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String, nullable=False)  # ссылка на аудио
    status: Mapped[str] = mapped_column(String, default="queued")  # queued / processing / done / error
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # результат транскрипции
