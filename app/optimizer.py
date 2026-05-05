import random
import numpy as np


def calculate_distance(point_a, point_b):
    return np.sqrt((point_a.x - point_b.x) ** 2 + (point_a.y - point_b.y) ** 2)


def build_distance_matrix(points):
    size = len(points)
    matrix = np.zeros((size, size))

    for i in range(size):
        for j in range(i + 1, size):
            distance = calculate_distance(points[i], points[j])
            matrix[i][j] = distance
            matrix[j][i] = distance

    return matrix


def calculate_total_distance(points, return_to_start=True):
    if len(points) < 2:
        return 0

    matrix = build_distance_matrix(points)
    route = list(range(len(points)))

    return calculate_route_distance(route, matrix, return_to_start)


def calculate_route_distance(route, distance_matrix, return_to_start=True):
    if len(route) < 2:
        return 0

    total = 0

    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i + 1]]

    if return_to_start:
        total += distance_matrix[route[-1]][route[0]]

    return total


def create_random_route_indices(points_count):
    if points_count <= 2:
        return list(range(points_count))

    start = 0
    rest = list(range(1, points_count))
    random.shuffle(rest)

    return [start] + rest


def create_initial_population(points_count, population_size):
    return [create_random_route_indices(points_count) for _ in range(population_size)]


def tournament_selection(population, distance_matrix, tournament_size=3):
    participants = random.sample(population, min(tournament_size, len(population)))
    participants.sort(key=lambda route: calculate_route_distance(route, distance_matrix))
    return participants[0][:]


def crossover(parent1, parent2):
    if len(parent1) <= 2:
        return parent1[:]

    start_point = parent1[0]
    p1 = parent1[1:]
    p2 = parent2[1:]

    size = len(p1)
    start_idx = random.randint(0, size - 1)
    end_idx = random.randint(start_idx, size - 1)

    child_middle = p1[start_idx:end_idx + 1]
    child_rest = [point for point in p2 if point not in child_middle]

    child = child_rest[:start_idx] + child_middle + child_rest[start_idx:]

    return [start_point] + child


def mutate(route, mutation_rate=0.1):
    if len(route) <= 2:
        return route

    mutated = route[:]

    for i in range(1, len(mutated)):
        if random.random() < mutation_rate:
            j = random.randint(1, len(mutated) - 1)
            mutated[i], mutated[j] = mutated[j], mutated[i]

    return mutated


def genetic_algorithm_route(points, population_size=100, generations=200, mutation_rate=0.1):
    if len(points) <= 2:
        return points[:], calculate_total_distance(points)

    distance_matrix = build_distance_matrix(points)
    population = create_initial_population(len(points), population_size)

    best_route_indices = min(
        population,
        key=lambda route: calculate_route_distance(route, distance_matrix)
    )
    best_distance = calculate_route_distance(best_route_indices, distance_matrix)

    for _ in range(generations):
        new_population = []

        elite = min(
            population,
            key=lambda route: calculate_route_distance(route, distance_matrix)
        )
        new_population.append(elite[:])

        while len(new_population) < population_size:
            parent1 = tournament_selection(population, distance_matrix)
            parent2 = tournament_selection(population, distance_matrix)

            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate)

            new_population.append(child)

        population = new_population

        current_best = min(
            population,
            key=lambda route: calculate_route_distance(route, distance_matrix)
        )
        current_distance = calculate_route_distance(current_best, distance_matrix)

        if current_distance < best_distance:
            best_route_indices = current_best[:]
            best_distance = current_distance

    best_route = [points[index] for index in best_route_indices]

    return best_route, best_distance