import random
import numpy as np
import requests
import folium

def calculate_distance(point_a, point_b):
    url = f"http://router.project-osrm.org/route/v1/driving/{point_a.lon},{point_a.lat};{point_b.lon},{point_b.lat}?overview=false"
    try:
        response = requests.get(url, timeout=2).json()
        if response['code'] == 'Ok':
            return response['routes'][0]['distance'] / 1000
    except:
        pass
    return np.sqrt((point_a.lat - point_b.lat) ** 2 + (point_a.lon - point_b.lon) ** 2) * 111

def calculate_total_distance(points, return_to_start=True):
    if len(points) < 2: return 0
    total = sum(calculate_distance(points[i], points[i + 1]) for i in range(len(points) - 1))
    if return_to_start:
        total += calculate_distance(points[-1], points[0])
    return total

def create_random_route(points):
    if len(points) <= 2: return points[:]
    start = points[0]
    rest = points[1:]; shuffled = rest[:]; random.shuffle(shuffled)
    return [start] + shuffled

def create_initial_population(points, population_size):
    return [create_random_route(points) for _ in range(population_size)]

def tournament_selection(population, tournament_size=3):
    participants = random.sample(population, min(tournament_size, len(population)))
    participants.sort(key=calculate_total_distance)
    return participants[0][:]

def crossover(parent1, parent2):
    if len(parent1) <= 2: return parent1[:]
    start_point = parent1[0]; p1 = parent1[1:]; p2 = parent2[1:]
    size = len(p1); start_idx = random.randint(0, size - 1); end_idx = random.randint(start_idx, size - 1)
    child_middle = p1[start_idx:end_idx + 1]
    child_rest = [point for point in p2 if point not in child_middle]
    child = child_rest[:start_idx] + child_middle + child_rest[start_idx:]
    return [start_point] + child

def mutate(route, mutation_rate=0.1):
    if len(route) <= 2: return route
    mutated = route[:]
    for i in range(1, len(mutated)):
        if random.random() < mutation_rate:
            j = random.randint(1, len(mutated) - 1)
            mutated[i], mutated[j] = mutated[j], mutated[i]
    return mutated

def genetic_algorithm_route(points, population_size=50, generations=50):
    if len(points) <= 2: return points[:], calculate_total_distance(points)
    def create_route():
        start = points[0]; others = points[1:]; shuffled = random.sample(others, len(others))
        return [start] + shuffled
    population = [create_route() for _ in range(population_size)]
    for _ in range(generations):
        population.sort(key=lambda r: calculate_total_distance(r))
        population = population[:population_size//2]
        while len(population) < population_size:
            p1, p2 = random.choice(population[:5]), random.choice(population[:5])
            child = p1[:len(p1)//2] + [pt for pt in p2 if pt not in p1[:len(p1)//2]]
            population.append(child)
    best_route = min(population, key=calculate_total_distance)
    return best_route, calculate_total_distance(best_route)


def get_osrm_route(point_a, point_b):
    url = f"http://router.project-osrm.org/route/v1/driving/{point_a.lon},{point_a.lat};{point_b.lon},{point_b.lat}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=5).json()
        if response['code'] == 'Ok':
            distance = response['routes'][0]['distance'] / 1000
            coords = [[lat, lon] for lon, lat in response['routes'][0]['geometry']['coordinates']]
            return distance, coords
    except: pass
    return None, None

def generate_map(ordered_points):
    if not ordered_points: return
    m = folium.Map(location=[ordered_points[0].lat, ordered_points[0].lon], zoom_start=13)
    for i, p in enumerate(ordered_points):
        folium.Marker([p.lat, p.lon], popup=f"{i}. {p.name}", icon=folium.Icon(color='green' if p.is_start else 'orange')).add_to(m)
    full_route = ordered_points + [ordered_points[0]]
    for i in range(len(full_route) - 1):
        _, route_coords = get_osrm_route(full_route[i], full_route[i+1])
        if route_coords: folium.PolyLine(route_coords, color="blue", weight=5).add_to(m)
    m.save("mapa_trasy.html")