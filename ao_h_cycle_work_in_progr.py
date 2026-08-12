import sys
sys.setrecursionlimit(10000)

def is_rigid(setup):
    """
    Helper function: checks if a hub has exactly 1 free edge.
    """
    n = len(setup)
    free_edges = 0
    for i in range(n):
        if setup[i] == setup[(i + 1) % n]:
            free_edges += 1
    return free_edges == 1


def generate_spoke_cycle(n, attempt=0):
    """
    Generates a Hamiltonian cycle through the spoke states using Warnsdorff's heuristic.
    Safely shifts the routing on new attempts by only offsetting ties.
    """
    total_states = 1 << n
    start_state = "0" * n
    path = [start_state]
    visited = {start_state}

    def get_neighbors(state):
        neighbors = []
        for i in range(n):
            flipped = '1' if state[i] == '0' else '0'
            neighbors.append(state[:i] + flipped + state[i + 1:])
        return neighbors

    def count_unvisited(state):
        return sum(1 for neighbor in get_neighbors(state) if neighbor not in visited)

    def explore(current_state):
        if len(path) == total_states:
            diff = sum(1 for a, b in zip(current_state, start_state) if a != b)
            return diff == 1

        valid_neighbors = [n for n in get_neighbors(current_state) if n not in visited]

        scored_neighbors = [(n, count_unvisited(n)) for n in valid_neighbors]

        scored_neighbors.sort(key=lambda x: x[1])

        if scored_neighbors:
            best_score = scored_neighbors[0][1]
            best_ties = [n for n, score in scored_neighbors if score == best_score]
            other_neighbors = [n for n, score in scored_neighbors if score != best_score]

            if len(best_ties) > 1:
                offset = (attempt + len(path)) % len(best_ties)
                best_ties = best_ties[offset:] + best_ties[:offset]

            valid_neighbors = best_ties + other_neighbors

        for next_state in valid_neighbors:
            visited.add(next_state)
            path.append(next_state)

            if explore(next_state):
                return True

            path.pop()
            visited.remove(next_state)

        return False

    explore(start_state)
    return path

def get_rigid_hubs(spoke_cycle):
    """
    Scans a list of spoke setups and returns only the rigid ones.
    A setup is rigid if it leaves exactly 1 free edge on the rim.
    """
    rigid_hubs = []
    n = len(spoke_cycle[0])

    for setup in spoke_cycle:
        free_edges = 0

        for i in range(n):
            current_spoke = setup[i]
            next_spoke = setup[(i + 1) % n]

            if current_spoke == next_spoke:
                free_edges += 1

        if free_edges == 1:
            rigid_hubs.append(setup)

    return rigid_hubs


def get_hub_pattern(setup):
    """
    Creates the X, 0, 1 constraint pattern for ANY hub setup.
    """
    n = len(setup)
    pattern = []

    for i in range(n):
        current_spoke = setup[i]
        next_spoke = setup[(i + 1) % n]

        if current_spoke == next_spoke:
            pattern.append('X')
        elif current_spoke == '0' and next_spoke == '1':
            pattern.append('1')
        elif current_spoke == '1' and next_spoke == '0':
            pattern.append('0')

    return "".join(pattern)


def get_all_hub_doors(pattern):
    """
    Generates all valid rim states for a room by filling in the 'X's.
    """
    free_indices = [i for i, char in enumerate(pattern) if char == 'X']
    total_states = 1 << len(free_indices)
    doors = []

    for i in range(total_states):
        binary_fill = f"{i:0{len(free_indices)}b}"
        door = list(pattern)

        for j, index in enumerate(free_indices):
            door[index] = binary_fill[j]

        doors.append("".join(door))

    return doors


def get_hub_doors(setup):
    """
    Calculates the pattern for a hub setup and returns its valid states (doors).
    Rule 1: If adjacent spokes match, the rim edge is free (X).
    Rule 2: If spoke goes 0->1, rim edge is fixed to 1.
    Rule 3: If spoke goes 1->0, rim edge is fixed to 0.
    """
    n = len(setup)
    pattern = []

    for i in range(n):
        current_spoke = setup[i]
        next_spoke = setup[(i + 1) % n]

        if current_spoke == next_spoke:
            pattern.append('X')
        elif current_spoke == '0' and next_spoke == '1':
            pattern.append('1')
        elif current_spoke == '1' and next_spoke == '0':
            pattern.append('0')

    door_0 = "".join(pattern).replace('X', '0')
    door_1 = "".join(pattern).replace('X', '1')

    return [door_0, door_1]


def get_shared_door(hub_a, hub_b, entry_door=None):
    """
    Finds a legally shared door between ANY two adjacent hubs.
    If an entry_door is provided, it strictly enforces the checkerboard rule:
    the chosen exit door MUST have an odd Hamming distance from the entry door.
    """
    pattern_a = get_hub_pattern(hub_a)
    pattern_b = get_hub_pattern(hub_b)

    doors_a = get_all_hub_doors(pattern_a)
    doors_b = get_all_hub_doors(pattern_b)

    shared_doors = [door for door in doors_a if door in doors_b]

    if not entry_door:
        return shared_doors[0] if shared_doors else None

    for door in shared_doors:
        distance = sum(1 for bit_a, bit_b in zip(door, entry_door) if bit_a != bit_b)

        if distance % 2 != 0:
            return door

    return None


def get_flexible_bridge(start_door, target_door, pattern):
    """
    Sweeps through the free edges to build a continuous path.
    Uses Warnsdorff's heuristic with a distance tie-breaker to prevent
    the engine from getting trapped.
    """
    free_indices = [i for i, char in enumerate(pattern) if char == 'X']
    total_states = 1 << len(free_indices)

    path = []
    visited = set()

    def get_valid_neighbors(current_state):
        neighbors = []
        for i in free_indices:
            flipped_bit = '1' if current_state[i] == '0' else '0'
            next_state = current_state[:i] + flipped_bit + current_state[i + 1:]

            if next_state == target_door and len(path) < total_states - 1:
                continue

            if next_state not in visited:
                neighbors.append(next_state)
        return neighbors

    def explore(current_state):
        path.append(current_state)
        visited.add(current_state)

        if len(path) == total_states:
            if current_state == target_door:
                return True
            else:
                visited.remove(current_state)
                path.pop()
                return False

        valid_neighbors = get_valid_neighbors(current_state)

        def count_unvisited(state):
            count = 0
            for i in free_indices:
                flipped_bit = '1' if state[i] == '0' else '0'
                next_state = state[:i] + flipped_bit + state[i + 1:]
                if next_state not in visited and next_state != target_door:
                    count += 1
            return count

        def distance_to_target(state):
            return sum(1 for a, b in zip(state, target_door) if a != b)

        valid_neighbors.sort(key=lambda s: (count_unvisited(s), -distance_to_target(s)))

        for next_state in valid_neighbors:
            if explore(next_state):
                return True

        visited.remove(current_state)
        path.pop()
        return False

    explore(start_door)
    return path


def build_master_cycle(n, attempt=0):
    """
    Attempts to string the rooms together. If a track fails, it increments the attempt
    to deterministically shift the Warnsdorff routing.
    """
    spoke_cycle = generate_spoke_cycle(n, attempt)

    if len(spoke_cycle) < (1 << n):
        print(f"The generator could not find a valid sequence.",flush=True)
        return None

    print(f"Starting Engine for W_{n}...",flush=True)
    print(f"Total Hub Rooms to visit: {len(spoke_cycle)}",flush=True)

    pattern_last = get_hub_pattern(spoke_cycle[-1])
    pattern_first = get_hub_pattern(spoke_cycle[0])
    doors_last = get_all_hub_doors(pattern_last)
    doors_first = get_all_hub_doors(pattern_first)

    possible_start_doors = [d for d in doors_last if d in doors_first]

    for start_door in possible_start_doors:
        print(f"Attempting track starting with door: {start_door}...",flush=True)

        full_hamiltonian_cycle = []
        current_entry_door = start_door
        track_failed = False

        for i in range(len(spoke_cycle)):
            current_hub = spoke_cycle[i]
            next_hub = spoke_cycle[(i + 1) % len(spoke_cycle)]
            pattern = get_hub_pattern(current_hub)

            if i == len(spoke_cycle) - 1:
                current_exit_door = start_door
            else:
                current_exit_door = get_shared_door(current_hub, next_hub, entry_door=current_entry_door)

            if not current_exit_door:
                track_failed = True
                break

            room_path = get_flexible_bridge(current_entry_door, current_exit_door, pattern)

            if not room_path:
                track_failed = True
                break

            if i < len(spoke_cycle) - 1:
                for rim_state in room_path[:-1]:
                    full_hamiltonian_cycle.append(f"Hub:{current_hub} Rim:{rim_state}")
            else:
                for rim_state in room_path:
                    full_hamiltonian_cycle.append(f"Hub:{current_hub} Rim:{rim_state}")

            current_entry_door = current_exit_door

        if not track_failed:
            return full_hamiltonian_cycle

    print("Exhausted all starting doors. The hub sequence itself is incompatible.",flush=True)
    return None


n = 5
attempt = 0
final_cycle = None


while not final_cycle:
    print(f"\n--- Sequence Generation Attempt {attempt} ---",flush=True)
    final_cycle = build_master_cycle(n, attempt)

    if not final_cycle:
        print("Master Parity check failed. Shifting routing and recalculating...",flush=True)
        attempt += 1

print(f"\nSUCCESS! Generated Hamiltonian Cycle with {len(final_cycle)} states on Attempt {attempt}.")

