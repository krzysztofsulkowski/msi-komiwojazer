from dataclasses import dataclass


@dataclass
class Point:
    name: str
    lat: float
    lon: float
    is_start: bool = False