from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False) # ссылка на аудио
    status = Column(String, default="queued") # queued / processing / done / error
    transcription = Column(Text, nullable=True) # результат транскрипции
