def route_cost(distances, depot, clients):
    if not clients:
        return 0

    path = [depot, *clients, depot]
    return sum(distances[start][finish] for start, finish in zip(path, path[1:]))


def replan_routes(distances, original_routes, removed_clients, max_clients, max_steps=30):
    removed = set(removed_clients)
    updated_routes = {
        depot: [[client for client in route if client not in removed] for route in routes]
        for depot, routes in original_routes.items()
    }
    vehicles = [(depot, route) for depot, routes in updated_routes.items() for route in routes]

    for _ in range(max_steps):
        best_delta = 0
        best_change = None

        for source_id, (source_depot, source_route) in enumerate(vehicles):
            for source_pos, client in enumerate(source_route):
                previous = source_route[source_pos - 1] if source_pos else source_depot
                following = source_route[source_pos + 1] if source_pos + 1 < len(source_route) else source_depot
                removal_delta = (
                    distances[previous][following]
                    - distances[previous][client]
                    - distances[client][following]
                )
                shortened_route = source_route[:source_pos] + source_route[source_pos + 1:]

                for target_id, (target_depot, target_route) in enumerate(vehicles):
                    if source_id != target_id and len(target_route) >= max_clients:
                        continue

                    candidate_route = shortened_route if source_id == target_id else target_route
                    for target_pos in range(len(candidate_route) + 1):
                        left = candidate_route[target_pos - 1] if target_pos else target_depot
                        right = candidate_route[target_pos] if target_pos < len(candidate_route) else target_depot
                        delta = (
                            removal_delta
                            + distances[left][client]
                            + distances[client][right]
                            - distances[left][right]
                        )
                        if delta < best_delta - 1e-12:
                            best_delta = delta
                            best_change = ('move', source_id, source_pos, target_id, target_pos)

        for first_id, (first_depot, first_route) in enumerate(vehicles):
            for second_id in range(first_id + 1, len(vehicles)):
                second_depot, second_route = vehicles[second_id]

                for first_pos, first_client in enumerate(first_route):
                    first_left = first_route[first_pos - 1] if first_pos else first_depot
                    first_right = first_route[first_pos + 1] if first_pos + 1 < len(first_route) else first_depot

                    for second_pos, second_client in enumerate(second_route):
                        second_left = second_route[second_pos - 1] if second_pos else second_depot
                        second_right = second_route[second_pos + 1] if second_pos + 1 < len(second_route) else second_depot

                        delta = (
                            distances[first_left][second_client]
                            + distances[second_client][first_right]
                            + distances[second_left][first_client]
                            + distances[first_client][second_right]
                            - distances[first_left][first_client]
                            - distances[first_client][first_right]
                            - distances[second_left][second_client]
                            - distances[second_client][second_right]
                        )
                        if delta < best_delta - 1e-12:
                            best_delta = delta
                            best_change = ('swap', first_id, first_pos, second_id, second_pos)

        for vehicle_id, (depot, route) in enumerate(vehicles):
            reversed_prefix = [0]
            for first_client, second_client in zip(route, route[1:]):
                reversed_prefix.append(
                    reversed_prefix[-1]
                    + distances[second_client][first_client]
                    - distances[first_client][second_client]
                )

            for start_pos in range(len(route)):
                for end_pos in range(start_pos + 1, len(route)):
                    previous = route[start_pos - 1] if start_pos else depot
                    following = route[end_pos + 1] if end_pos + 1 < len(route) else depot
                    first_client = route[start_pos]
                    last_client = route[end_pos]
                    delta = (
                        distances[previous][last_client]
                        + distances[first_client][following]
                        - distances[previous][first_client]
                        - distances[last_client][following]
                        + reversed_prefix[end_pos]
                        - reversed_prefix[start_pos]
                    )
                    if delta < best_delta - 1e-12:
                        best_delta = delta
                        best_change = ('reverse', vehicle_id, start_pos, end_pos)

        if best_change is None:
            break

        operation, *positions = best_change
        if operation == 'move':
            source_id, source_pos, target_id, target_pos = positions
            client = vehicles[source_id][1].pop(source_pos)
            vehicles[target_id][1].insert(target_pos, client)
        elif operation == 'swap':
            first_id, first_pos, second_id, second_pos = positions
            first_route = vehicles[first_id][1]
            second_route = vehicles[second_id][1]
            first_route[first_pos], second_route[second_pos] = second_route[second_pos], first_route[first_pos]
        else:
            vehicle_id, start_pos, end_pos = positions
            route = vehicles[vehicle_id][1]
            route[start_pos:end_pos + 1] = reversed(route[start_pos:end_pos + 1])

    return updated_routes
