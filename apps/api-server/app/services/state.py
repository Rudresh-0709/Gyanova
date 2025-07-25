from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class Slide(BaseModel):
    title:Optional[str]=None
    narration:Optional[str]=None

    audio_url:Optional[str]=None
    image_url:Optional[str]=None

class TutorState(BaseModel):
    user_input:Optional[str]=None
    topic:Optional[str]=None
    topic_granularity:Optional[str]=None
    sub_topics:Optional[List[str]]=None
    preffered_method:Optional[str]=None

    teacher_id:Optional[int]=None
    teacher_voice_id:Optional[int]=None
    teacher_gender:Optional[str]="Male"

    current_slide:Optional[int]=0
    slides:Optional[Slide]=None

    user_interruption:Optional[str]=None
    ai_response:Optional[str]=None
    last_completed_node:Optional[str]=None

    error:Optional[str]=None

    is_paused:Optional[bool]=False
    timestamp:Optional[str]=None