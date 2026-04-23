from dataclasses import dataclass


@dataclass
class Point:
    name: str
    x: float
    y: float
    is_start: bool = False