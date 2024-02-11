import dataclasses
import datetime as dt
from abc import ABC
from typing import Optional


@dataclasses.dataclass
class CameraState:
    recording: Optional[bool]
    remaining: Optional[dt.timedelta]


class CameraControl(ABC):
    def __open__(self):
        pass

    def prepare(self):
        pass

    def get_state(self) -> CameraState:
        pass

    def video_record_start(self):
        pass

    def video_record_stop(self):
        pass