from dataclasses import dataclass


@dataclass
class Point:
    name: str
    latitude: float
    longitude: float
    x: float
    y: float
    address: str = ""
    comment: str = ""
    is_start: bool = False
    delivered: bool = False