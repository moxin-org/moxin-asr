from enum import Enum

import numpy as np
from pydantic import BaseModel, Field


class VoiceTask(BaseModel):
    """语音任务模型"""

    id: str

    session_id: str = Field(default="")
    language: str = Field(default="zh")
    is_speaking_over_threshold: bool = Field(default=False)
    is_over_audio_frames_threshold: bool = Field(default=False)
    user_voice: np.array = Field(default=np.array([]))

    send_time: float = Field(default=0)
    whisper_start_time: float = Field(default=0)
    whisper_end_time: float = Field(default=0)
    llm_start_time: float = Field(default=0)
    llm_end_time: float = Field(default=0)
    tts_start_time: float = Field(default=0)
    tts_end_time: float = Field(default=0)

    transcribed_text: str = Field(default="")

    answer_id: str = Field(default="")
    answer_index: int = Field(default=0)
    answer_sentence: str = Field(default="")
    tts_generated_sentence_audio: tuple = Field(default=())

    class Config:
        arbitrary_types_allowed = True


class DisplayMessageType(str, Enum):
    QUESTION = 'question'
    ANSWER = 'answer'


class BaseDisplayMessage(BaseModel):
    message_type: DisplayMessageType
    session_id: str
    task_id: str


class QuestionDisplayMessage(BaseDisplayMessage):
    message_type: DisplayMessageType = DisplayMessageType.QUESTION
    question: str


class AnswerDisplayMessage(BaseDisplayMessage):
    message_type: DisplayMessageType = DisplayMessageType.ANSWER
    answer_index: int
    answer: str
