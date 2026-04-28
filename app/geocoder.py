from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError


LEGNICA_BOUNDS = {
    "min_latitude": 51.18,
    "max_latitude": 51.23,
    "min_longitude": 16.11,
    "max_longitude": 16.21
}


def is_location_in_legnica_area(latitude, longitude):
    return (
        LEGNICA_BOUNDS["min_latitude"] <= latitude <= LEGNICA_BOUNDS["max_latitude"]
        and LEGNICA_BOUNDS["min_longitude"] <= longitude <= LEGNICA_BOUNDS["max_longitude"]
    )


def search_address(address, limit=5):
    if not address or not address.strip():
        return {
            "success": False,
            "message": "Wpisz adres do wyszukania",
            "results": []
        }

    geolocator = Nominatim(
        user_agent="msi_komiwojazer_legnica_project",
        timeout=10
    )

    query = address.strip()

    if "legnica" not in query.lower():
        query = f"{query}, Legnica, Polska"

    try:
        locations = geolocator.geocode(
            query,
            exactly_one=False,
            limit=limit,
            country_codes="pl"
        )
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError):
        return {
            "success": False,
            "message": "Nie udało się połączyć z geocoderem",
            "results": []
        }

    if not locations:
        return {
            "success": False,
            "message": "Nie znaleziono adresu",
            "results": []
        }

    results = []

    for location in locations:
        latitude = float(location.latitude)
        longitude = float(location.longitude)

        if is_location_in_legnica_area(latitude, longitude):
            results.append(
                {
                    "address": location.address,
                    "latitude": latitude,
                    "longitude": longitude
                }
            )

    if not results:
        return {
            "success": False,
            "message": "Znaleziono adres, ale poza obsługiwanym obszarem Legnicy",
            "results": []
        }

    return {
        "success": True,
        "message": f"Znaleziono {len(results)} wyników",
        "results": results
    }