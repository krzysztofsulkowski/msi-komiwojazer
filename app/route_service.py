import requests


road_route_cache = {}


def get_route_cache_key(point_a, point_b):
    return (
        round(point_a.latitude, 6),
        round(point_a.longitude, 6),
        round(point_b.latitude, 6),
        round(point_b.longitude, 6)
    )


def get_road_route_between_points(point_a, point_b):
    cache_key = get_route_cache_key(point_a, point_b)

    if cache_key in road_route_cache:
        return road_route_cache[cache_key]

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{point_a.longitude},{point_a.latitude};"
        f"{point_b.longitude},{point_b.latitude}"
        "?overview=full&geometries=geojson"
    )

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("code") != "Ok":
            return None, None

        route = data["routes"][0]
        distance_km = route["distance"] / 1000

        coordinates = [
            (latitude, longitude)
            for longitude, latitude in route["geometry"]["coordinates"]
        ]

        result = (distance_km, coordinates)
        road_route_cache[cache_key] = result

        return result
    except requests.RequestException:
        return None, None
    except (KeyError, IndexError, TypeError):
        return None, None