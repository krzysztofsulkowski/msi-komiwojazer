import json
from datetime import datetime
from app.models import Point
from app.optimizer import calculate_total_distance


def export_route_to_json(points, file_path):
    data = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "route_type": "optimized" if len(points) > 1 else "not_optimized",
        "total_distance": calculate_total_distance(points),
        "depot": None,
        "locations": []
    }

    for index, point in enumerate(points):
        point_data = {
            "order": index,
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

        if point.is_start:
            data["depot"] = point_data
        else:
            data["locations"].append(point_data)

    data["route"] = []

    if data["depot"]:
        data["route"].append(data["depot"])

    data["route"].extend(data["locations"])

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def import_route_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    points = []

    route_items = data.get("route", [])

    if not route_items:
        depot = data.get("depot")
        locations = data.get("locations", [])

        if depot:
            route_items.append(depot)

        route_items.extend(locations)

    for item in route_items:
        point = Point(
            name=item.get("name", ""),
            latitude=float(item.get("latitude", 0)),
            longitude=float(item.get("longitude", 0)),
            x=float(item.get("x", 0)),
            y=float(item.get("y", 0)),
            address=item.get("address", ""),
            comment=item.get("comment", ""),
            is_start=bool(item.get("is_start", False)),
            delivered=bool(item.get("delivered", False))
        )

        points.append(point)

    points.sort(key=lambda point: 0 if point.is_start else 1)

    return points