import itertools, math

# Global cache for distances
distance_cache = {}

def calculate_distance(p1, p2, points):
    if (p1, p2) in distance_cache:
        return distance_cache[(p1, p2)]
    x1, y1 = points[p1]["x"], points[p1]["y"]
    x2, y2 = points[p2]["x"], points[p2]["y"]
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_cache[(p1, p2)] = dist
    distance_cache[(p2, p1)] = dist
    return dist

def find_closest_pickup(last_point, start_points, points):
    closest, min_d = None, float('inf')
    for s in start_points:
        d = calculate_distance(s, last_point, points)
        if d < min_d:
            min_d = d
            closest = s
    return closest

def calculate_path_distance_with_pickup(path, min_distance_threshold, start_points, points):
    total = 0
    for i in range(len(path) - 2):  # Check all segments except the final one
        seg = calculate_distance(path[i], path[i+1], points)
        if seg < min_distance_threshold:
            return None, None
        total += seg
    last = path[-1]
    pickup = find_closest_pickup(last, start_points, points)
    total += calculate_distance(last, pickup, points)
    return total, pickup

def generate_paths(points, min_distance_threshold, max_total_distance, number_points):
    # Assume start points have IDs 'N', 'S', 'E', 'W'
    start_points = [p for p in points if p in ['N', 'S', 'E', 'W']]
    num_points = [p for p in points if p not in ['N', 'S', 'E', 'W']]
    valid_paths = []
    seen_first_two = set()
    for s in start_points:
        # Use the dynamic number of numbered points in the permutation
        for path in itertools.permutations(num_points, number_points):
            full_path = (s,) + path
            total, pickup = calculate_path_distance_with_pickup(full_path, min_distance_threshold, start_points, points)
            if total is not None and total < max_total_distance:
                key = (full_path[0], full_path[1])
                if key not in seen_first_two:
                    seen_first_two.add(key)
                    valid_paths.append((full_path + (pickup,), total))
    return valid_paths

