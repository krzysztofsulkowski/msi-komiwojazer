import random
import numpy as np


def calculate_distance(point_a, point_b):
    return np.sqrt((point_a.x - point_b.x) ** 2 + (point_a.y - point_b.y) ** 2)


def calculate_total_distance(points):
    if len(points) < 2:
        return 0

    total = 0

    for i in range(len(points) - 1):
        total += calculate_distance(points[i], points[i + 1])

    return total


def create_random_route(points):
    if len(points) <= 2:
        return points[:]

    start = points[0]
    rest = points[1:]
    shuffled = rest[:]
    random.shuffle(shuffled)
    return [start] + shuffled


def create_initial_population(points, population_size):
    return [create_random_route(points) for _ in range(population_size)]


def tournament_selection(population, tournament_size=3):
    participants = random.sample(population, min(tournament_size, len(population)))
    participants.sort(key=calculate_total_distance)
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

    population = create_initial_population(points, population_size)
    best_route = min(population, key=calculate_total_distance)
    best_distance = calculate_total_distance(best_route)

    for _ in range(generations):
        new_population = []

        elite = min(population, key=calculate_total_distance)
        new_population.append(elite[:])

        while len(new_population) < population_size:
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)

            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate)

            new_population.append(child)

        population = new_population

        current_best = min(population, key=calculate_total_distance)
        current_distance = calculate_total_distance(current_best)

        if current_distance < best_distance:
            best_route = current_best[:]
            best_distance = current_distance

    return best_route, best_distance