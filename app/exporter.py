import json
from app.optimizer import calculate_total_distance


def export_route_to_json(points, file_path):
    data = {
        "distance": calculate_total_distance(points),
        "route": [
            {
                "name": point.name,
                "address": point.address,
                "comment": point.comment,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "x": point.x,
                "y": point.y,
                "is_start": point.is_start,
                "delivered": point.delivered
            }
            for point in points
        ]
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)