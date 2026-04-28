import json
from app.optimizer import calculate_total_distance


def export_route_to_json(points, file_path):
    data = {
        "distance": calculate_total_distance(points),
        "route": [
            {
                "name": point.name,
                "x": point.x,
                "y": point.y,
                "is_start": point.is_start
            }
            for point in points
        ]
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)