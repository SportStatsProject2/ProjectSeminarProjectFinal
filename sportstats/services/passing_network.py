from __future__ import annotations

from collections import defaultdict
import json


DEMO_PASSES = [
    {"passer": "GK", "receiver": "LCB", "start_x": 8, "start_y": 48, "end_x": 24, "end_y": 30},
    {"passer": "GK", "receiver": "RCB", "start_x": 8, "start_y": 52, "end_x": 24, "end_y": 70},
    {"passer": "LCB", "receiver": "DM", "start_x": 24, "start_y": 30, "end_x": 42, "end_y": 48},
    {"passer": "LCB", "receiver": "LB", "start_x": 25, "start_y": 28, "end_x": 38, "end_y": 16},
    {"passer": "LB", "receiver": "LW", "start_x": 38, "start_y": 16, "end_x": 66, "end_y": 18},
    {"passer": "LW", "receiver": "LB", "start_x": 66, "start_y": 18, "end_x": 40, "end_y": 18},
    {"passer": "RCB", "receiver": "DM", "start_x": 24, "start_y": 70, "end_x": 42, "end_y": 52},
    {"passer": "RCB", "receiver": "RB", "start_x": 25, "start_y": 72, "end_x": 38, "end_y": 84},
    {"passer": "RB", "receiver": "RW", "start_x": 38, "start_y": 84, "end_x": 66, "end_y": 82},
    {"passer": "RW", "receiver": "RB", "start_x": 66, "start_y": 82, "end_x": 40, "end_y": 82},
    {"passer": "DM", "receiver": "CM", "start_x": 43, "start_y": 50, "end_x": 55, "end_y": 50},
    {"passer": "CM", "receiver": "AM", "start_x": 55, "start_y": 50, "end_x": 66, "end_y": 50},
    {"passer": "CM", "receiver": "DM", "start_x": 55, "start_y": 50, "end_x": 43, "end_y": 50},
    {"passer": "AM", "receiver": "ST", "start_x": 66, "start_y": 50, "end_x": 84, "end_y": 50},
    {"passer": "AM", "receiver": "LW", "start_x": 66, "start_y": 49, "end_x": 73, "end_y": 22},
    {"passer": "AM", "receiver": "RW", "start_x": 66, "start_y": 51, "end_x": 73, "end_y": 78},
    {"passer": "ST", "receiver": "AM", "start_x": 84, "start_y": 50, "end_x": 67, "end_y": 50},
    {"passer": "CM", "receiver": "LB", "start_x": 55, "start_y": 49, "end_x": 40, "end_y": 18},
    {"passer": "CM", "receiver": "RB", "start_x": 55, "start_y": 51, "end_x": 40, "end_y": 82},
    {"passer": "LB", "receiver": "CM", "start_x": 40, "start_y": 18, "end_x": 55, "end_y": 49},
    {"passer": "RB", "receiver": "CM", "start_x": 40, "start_y": 82, "end_x": 55, "end_y": 51},
    {"passer": "DM", "receiver": "AM", "start_x": 42, "start_y": 50, "end_x": 66, "end_y": 50},
    {"passer": "AM", "receiver": "ST", "start_x": 66, "start_y": 50, "end_x": 84, "end_y": 50},
    {"passer": "DM", "receiver": "AM", "start_x": 44, "start_y": 50, "end_x": 66, "end_y": 51},
    {"passer": "LCB", "receiver": "DM", "start_x": 25, "start_y": 31, "end_x": 43, "end_y": 49},
    {"passer": "RCB", "receiver": "DM", "start_x": 25, "start_y": 69, "end_x": 43, "end_y": 51},
]


def build_demo_network() -> dict:
    return build_network(DEMO_PASSES)


def demo_passes_json() -> str:
    return json.dumps(DEMO_PASSES, indent=2)


def parse_pass_events(raw_events: str) -> list[dict]:
    if not raw_events.strip():
        return []
    try:
        payload = json.loads(raw_events)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON is invalid near line {exc.lineno}, column {exc.colno}.") from exc

    if isinstance(payload, dict):
        payload = payload.get("passes")
    if not isinstance(payload, list):
        raise ValueError("Pass data must be a JSON array, or an object with a passes array.")
    return payload


def build_network(events: list[dict]) -> dict:
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    player_positions: dict[str, list[tuple[float, float]]] = defaultdict(list)
    passes_sent: dict[str, int] = defaultdict(int)
    passes_received: dict[str, int] = defaultdict(int)
    edge_counts: dict[tuple[str, str], int] = defaultdict(int)
    edge_progression: dict[tuple[str, str], list[float]] = defaultdict(list)
    progressions = []

    for event in events:
        passer = _required_text(event, "passer")
        receiver = _required_text(event, "receiver")
        start = (_required_number(event, "start_x"), _required_number(event, "start_y"))
        end = (_required_number(event, "end_x"), _required_number(event, "end_y"))
        progression = end[0] - start[0]
        player_positions[passer].append(start)
        player_positions[receiver].append(end)
        passes_sent[passer] += 1
        passes_received[receiver] += 1
        edge_counts[(passer, receiver)] += 1
        edge_progression[(passer, receiver)].append(progression)
        progressions.append(progression)

    nodes = []
    for player, positions in player_positions.items():
        avg_x = sum(position[0] for position in positions) / len(positions)
        avg_y = sum(position[1] for position in positions) / len(positions)
        touches = passes_sent[player] + passes_received[player]
        nodes.append(
            {
                "player": player,
                "x": round(avg_x, 1),
                "y": round(avg_y, 1),
                "passes_sent": passes_sent[player],
                "passes_received": passes_received[player],
                "touches": touches,
                "radius": round(2.7 + min(touches, 22) * 0.22, 1),
            }
        )

    node_lookup = {node["player"]: node for node in nodes}
    edges = []
    for (source, target), count in edge_counts.items():
        average_progression = sum(edge_progression[(source, target)]) / count
        edges.append(
            {
                "source": source,
                "target": target,
                "source_x": node_lookup[source]["x"],
                "source_y": node_lookup[source]["y"],
                "target_x": node_lookup[target]["x"],
                "target_y": node_lookup[target]["y"],
                "count": count,
                "average_progression": round(average_progression, 1),
                "width": round(0.8 + min(count, 8) * 0.45, 1),
            }
        )
    sorted_nodes = sorted(nodes, key=lambda node: (-node["touches"], node["player"]))
    sorted_edges = sorted(edges, key=lambda edge: (-edge["count"], edge["source"], edge["target"]))
    total_passes = sum(edge["count"] for edge in edges)
    player_count = len(nodes)
    possible_links = player_count * (player_count - 1)
    progressive_passes = sum(1 for progression in progressions if progression >= 10)
    warnings = []
    if player_count > 11:
        warnings.append(f"{player_count} players are present in this data. Filter to one team/lineup for a standard XI view.")

    return {
        "nodes": sorted(nodes, key=lambda node: node["player"]),
        "edges": sorted_edges,
        "top_nodes": sorted_nodes,
        "total_passes": total_passes,
        "player_count": player_count,
        "link_count": len(edges),
        "network_density": round((len(edges) / possible_links) * 100, 1) if possible_links else 0.0,
        "progressive_passes": progressive_passes,
        "average_progression": round(sum(progressions) / total_passes, 1) if total_passes else 0.0,
        "central_player": sorted_nodes[0]["player"] if sorted_nodes else "N/A",
        "warnings": warnings,
        "has_events": total_passes > 0,
    }


def _required_text(event: dict, key: str) -> str:
    value = event.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _required_number(event: dict, key: str) -> float:
    try:
        value = float(event[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be numeric") from exc
    if value < 0 or value > 100:
        raise ValueError(f"{key} must be between 0 and 100")
    return value
