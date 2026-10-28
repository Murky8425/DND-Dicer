"""Generate small, self-contained fantasy encounter maps as SVG images."""

import html
import math
import random
from collections.abc import Callable

# Diese Zahlen legen fest, wie groß die Karten und ihre Kästchen sind.
CELL_SIZE = 40
MAP_OPTION_COUNT = 8
DEFAULT_CHUNK_SIZE = (25, 15)
CHUNK_SIZE_OPTIONS = ((10, 10), (20, 20), DEFAULT_CHUNK_SIZE, (50, 50), (75, 75))

# Jede Karte bekommt einen passenden Namen und einen kurzen Erklärungssatz.
MAP_NAMES = {
    "Verlies": [
        "Die vergessene Gruft",
        "Krypta der Asche",
        "Der versiegelte Kerker",
    ],
    "Wald": [
        "Der Pfad im Nebelwald",
        "Lichtung der alten Eiche",
        "Der verwachsene Hohlweg",
    ],
    "Höhle": [
        "Die Kristallhöhle",
        "Tiefen unter dem Gebirge",
        "Die Echo-Grotte",
    ],
    "Eishöhle": [
        "Die Frostkammer",
        "Der blaue Gletscherstollen",
        "Die Halle der Eiszapfen",
    ],
    "Vulkanhöhle": [
        "Die Glutkluft",
        "Der Schlot der alten Bestie",
        "Die Magmakammer",
    ],
    "Pflanzenhöhle": [
        "Der grüne Schlund",
        "Die Wurzelgrotte",
        "Der Garten unter Stein",
    ],
    "Ruinen": [
        "Der versunkene Tempel",
        "Ruinen von Dornwacht",
        "Die zerbrochene Festung",
    ],
}

MAP_DESCRIPTIONS = {
    "Verlies": "Verbundene Kammern und steinerne Gänge",
    "Wald": "Ein verschlungener Pfad zwischen dichtem Gehölz",
    "Höhle": "Ein gewundener Gang durch die Felsen",
    "Eishöhle": "Vereiste Gänge und scharfkantige Eisformationen",
    "Vulkanhöhle": "Dunkle Felsen, heiße Schlote und glühende Lava",
    "Pflanzenhöhle": "Ein überwucherter Pfad durch unterirdisches Grün",
    "Ruinen": "Ein alter Weg zwischen eingestürzten Mauern",
}

MapBuilder = Callable[
    [random.Random, int, str, tuple[int, int], int, str, int],
    tuple[str, list[dict[str, object]], list[tuple[int, int]]],
]


# Diese Helfer malen Linien, Wege und andere kleine Kartenteile.
def _grid(color: str, map_size: tuple[int, int], opacity: float = 0.28) -> str:
    width, height = map_size
    lines = [
        f'<path d="M {x} 0 V {height}" />'
        for x in range(0, width + 1, CELL_SIZE)
    ]
    lines.extend(
        f'<path d="M 0 {y} H {width}" />'
        for y in range(0, height + 1, CELL_SIZE)
    )
    return (
        f'<g class="map-grid" fill="none" stroke="{color}" '
        f'stroke-width="1" opacity="{opacity}">'
        + "".join(lines)
        + "</g>"
    )


def _polyline(points: list[tuple[int, int]]) -> str:
    return " ".join(f"{x},{y}" for x, y in points)


def _distance_to_path(point: tuple[int, int], path: list[tuple[int, int]]) -> float:
    # Prüft, wie weit ein Punkt vom Weg entfernt ist, damit Deko nicht im Weg liegt.
    px, py = point
    minimum = float("inf")
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        dx, dy = x2 - x1, y2 - y1
        length_squared = dx * dx + dy * dy
        if length_squared == 0:
            distance = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        else:
            position = max(
                0,
                min(1, ((px - x1) * dx + (py - y1) * dy) / length_squared),
            )
            closest_x = x1 + position * dx
            closest_y = y1 + position * dy
            distance = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
        minimum = min(minimum, distance)
    return minimum


def _route_paths(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
) -> tuple[list[tuple[int, int]], list[list[tuple[int, int]]]]:
    # Erst wird der Hauptweg gebaut, danach kommen die kleinen Abzweigungen dazu.
    width, height = map_size
    main_path = [(0, rng.randint(round(height * 0.3), round(height * 0.7)))]
    center_index = (waypoint_count + 1) // 2
    for index in range(1, waypoint_count + 1):
        x = round(width * index / (waypoint_count + 1))
        y = rng.randint(round(height * 0.18), round(height * 0.82))
        if layout == "Kreuzung" and index == center_index:
            x, y = width // 2, height // 2
        main_path.append((x, y))
    main_path.append((width, rng.randint(round(height * 0.3), round(height * 0.7))))

    branches = []
    if layout == "Kreuzung":
        center = (width // 2, height // 2)
        branches.append([(center[0], 0), center, (center[0], height)])
    for index in range(branch_count):
        segment_position = (index + 0.5) * (len(main_path) - 1) / max(1, branch_count)
        segment_index = min(int(segment_position), len(main_path) - 2)
        fraction = rng.uniform(0.3, 0.7)
        start = main_path[segment_index]
        end = main_path[segment_index + 1]
        attach_x = round(start[0] + (end[0] - start[0]) * fraction)
        attach_y = round(start[1] + (end[1] - start[1]) * fraction)
        end_x = max(CELL_SIZE, min(width - CELL_SIZE, attach_x + rng.randint(-width // 8, width // 8)))
        edge_y = 0 if rng.choice((True, False)) else height
        branches.append([(attach_x, attach_y), (end_x, edge_y)])
    return main_path, branches


def _path_svg(paths: list[list[tuple[int, int]]], color: str, width: int) -> str:
    return "".join(
        f'<polyline points="{_polyline(path)}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" />'
        for path in paths
    )


def _encounter_marker_svg(
    route: list[tuple[int, int]],
    map_size: tuple[int, int],
) -> tuple[str, list[dict[str, int | str]]]:
    # Setzt Start, Begegnung, Gefahr und Schatz auf den Weg.
    if len(route) < 3:
        return "", []

    width, height = map_size
    if len(route) == 3:
        marker_specs = (
            ("start", "Start", "S", "#287a55", 0),
            ("encounter", "Begegnung", "B", "#b94c35", 1),
            ("treasure", "Schatz", "T", "#a77a17", 2),
        )
    else:
        last_index = len(route) - 1
        marker_specs = (
            ("start", "Start", "S", "#287a55", 0),
            ("encounter", "Begegnung", "B", "#b94c35", round(last_index / 3)),
            ("danger", "Gefahr", "G", "#68449b", round(2 * last_index / 3)),
            ("treasure", "Schatz", "T", "#a77a17", last_index),
        )

    groups = []
    marker_data = []
    for kind, label, symbol, color, index in marker_specs:
        x, y = route[index]
        marker_data.append(
            {"id": f"encounter-{kind}", "type": kind, "label": label, "x": x, "y": y}
        )
        display_x = max(18, min(width - 18, x))
        display_y = max(18, min(height - 18, y))
        label_x = 24 if display_x < width - 140 else -136
        groups.append(
            f'<g class="encounter-point" data-point-id="encounter-{kind}" '
            f'data-encounter-point="{kind}" '
            f'transform="translate({display_x} {display_y})" pointer-events="none">'
            f'<circle r="18" fill="{color}" stroke="#fff" stroke-width="4" />'
            f'<text y="6" text-anchor="middle" fill="#fff" font-size="17" '
            f'font-weight="bold">{symbol}</text>'
            f'<rect x="{label_x}" y="-14" width="112" height="28" rx="8" '
            f'fill="{color}" stroke="#fff" stroke-width="2" />'
            f'<text x="{label_x + 56}" y="5" text-anchor="middle" fill="#fff" '
            f'font-size="14" font-weight="bold">{html.escape(label)}</text>'
            "</g>"
        )
    return "".join(groups), marker_data


def _dungeon(
    rng: random.Random,
    room_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    # Baut ein Verlies mit Räumen, Gängen und optional runden Räumen.
    width, height = map_size
    room_centers, branches = _route_paths(
        rng,
        room_count - 2,
        layout,
        map_size,
        branch_count,
    )
    rooms: list[tuple[int, int, int, int, list[tuple[float, float]] | None]] = []
    spacing = width / max(1, len(room_centers) - 1)
    for room_index, (_, center_y) in enumerate(room_centers):
        center_x = round(
            CELL_SIZE / 2
            + (width - CELL_SIZE) * room_index / max(1, len(room_centers) - 1)
        )
        max_room_cells = max(1, min(4, int(spacing / CELL_SIZE * 0.9)))
        room_width = rng.randint(1, max_room_cells) * CELL_SIZE
        room_height = rng.randint(2, 3) * CELL_SIZE
        x = center_x - room_width // 2
        y = center_y - room_height // 2
        x = min(max(0, x), width - room_width)
        y = min(max(0, y), height - room_height)
        selected_shape = (
            rng.choice(("Eckig", "Organisch"))
            if room_shape == "Gemischt"
            else room_shape
        )
        shape_points = None
        if selected_shape == "Organisch":
            shape_points = []
            point_count = 8
            for point_index in range(point_count):
                angle = -math.pi / 2 + 2 * math.pi * point_index / point_count
                radius = rng.uniform(0.78, 1)
                shape_points.append((
                    round(0.5 + 0.48 * radius * math.cos(angle), 4),
                    round(0.5 + 0.48 * radius * math.sin(angle), 4),
                ))
        rooms.append((x, y, room_width, room_height, shape_points))
        room_centers[room_index] = (
            x + room_width // 2,
            y + room_height // 2,
        )

    corridors = []
    path_width = CELL_SIZE * corridor_width
    for path_index, path in enumerate([room_centers, *branches]):
        for (x1, y1), (x2, y2) in zip(path, path[1:]):
            bend_x = rng.choice((x1, x2))
            corridors.append(
                f'<path class="{"dungeon-corridor-main" if path_index == 0 else "dungeon-corridor-branch"}" '
                f'd="M {x1} {y1} H {bend_x} V {y2} H {x2}" '
                f'fill="none" stroke="#887d68" stroke-width="{path_width}" '
                'stroke-linecap="square" stroke-linejoin="round" />'
            )
    room_shapes = "".join(
        (
            f'<path class="dungeon-room" data-room-id="room-{index + 1}" '
            f'd="M {_polyline([(round(px * 1000), round(py * 1000)) for px, py in shape_points])} Z" '
            f'transform="translate({x} {y}) scale({room_width / 1000} {room_height / 1000})" '
            'fill="#887d68" stroke="#353832" stroke-width="7" />'
            if shape_points
            else
            f'<rect class="dungeon-room" data-room-id="room-{index + 1}" '
            f'x="{x}" y="{y}" width="{room_width}" height="{room_height}" '
            'rx="3" fill="#887d68" stroke="#353832" stroke-width="7" />'
        )
        for index, (x, y, room_width, room_height, shape_points) in enumerate(rooms)
    )
    svg_content = (
        f'<rect width="{width}" height="{height}" fill="#444740" />'
        + _grid("#c4b99e", map_size, 0.2)
        + f'<g class="dungeon-corridors" data-corridor-width="{path_width}">'
        + "".join(corridors)
        + "</g>"
        + room_shapes
        + _grid("#292d29", map_size, 0.25)
    )
    room_data = [
        {
            "id": f"room-{index + 1}",
            "x": x,
            "y": y,
            "width": room_width,
            "height": room_height,
            **({"shape_points": shape_points} if shape_points else {}),
        }
        for index, (x, y, room_width, room_height, shape_points) in enumerate(rooms)
    ]
    return svg_content, room_data, room_centers


def _forest(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    # Baut einen Waldweg und stellt Bäume daneben.
    del room_shape
    width, height = map_size
    path, branches = _route_paths(rng, waypoint_count, layout, map_size, branch_count)
    paths = [path, *branches]
    path_width = CELL_SIZE * corridor_width

    trees = []
    for _ in range(62):
        x = rng.randint(15, width - 15)
        y = rng.randint(15, height - 15)
        if any(_distance_to_path((x, y), route) < path_width / 2 + 20 for route in paths):
            continue
        radius = rng.randint(12, 21)
        trees.append(
            f'<circle cx="{x}" cy="{y}" r="{radius + 5}" fill="#173c31" />'
            f'<circle cx="{x - 3}" cy="{y - 4}" r="{radius}" fill="#32634b" '
            'stroke="#224c3b" stroke-width="3" />'
            f'<circle cx="{x - 7}" cy="{y - 9}" r="{radius // 3}" '
            'fill="#668457" opacity="0.8" />'
        )

    return (
        f'<rect width="{width}" height="{height}" fill="#526b48" />'
        + _grid("#d4c99c", map_size, 0.18)
        + _path_svg(paths, "#354832", path_width + 18)
        + _path_svg(paths, "#c3a979", path_width)
        + "".join(trees),
        [],
        path,
    )


def _cave(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
    variant: str = "Höhle",
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    # Baut Höhlenwege mit Felsen und zum Thema passenden Formationen.
    del room_shape
    width, height = map_size
    volcano_center = None
    lava_radii = None
    if variant == "Vulkanhöhle":
        center_x, center_y = width // 2, height // 2
        lake_radius_x = max(28, round(min(width * 0.16, height * 0.20)))
        lake_radius_y = max(28, round(min(height * 0.18, width * 0.18)))
        ring_radius_x = lake_radius_x + CELL_SIZE * corridor_width // 2 + 24
        ring_radius_y = lake_radius_y + CELL_SIZE * corridor_width // 2 + 24
        ring_path = [
            (
                round(center_x + ring_radius_x * math.cos(-math.pi / 2 + 2 * math.pi * index / 64)),
                round(center_y + ring_radius_y * math.sin(-math.pi / 2 + 2 * math.pi * index / 64)),
            )
            for index in range(65)
        ]
        road_y = ring_path[0][1]
        path = [(0, road_y), *ring_path, (width, road_y)]
        branches = []
        for index in range(branch_count):
            angle = 2 * math.pi * (index + 0.5) / branch_count
            direction_x = math.cos(angle)
            direction_y = math.sin(angle)
            attach = (
                round(center_x + ring_radius_x * direction_x),
                round(center_y + ring_radius_y * direction_y),
            )
            edge_distances = []
            if direction_x < 0:
                edge_distances.append((0 - attach[0]) / direction_x)
            elif direction_x > 0:
                edge_distances.append((width - attach[0]) / direction_x)
            if direction_y < 0:
                edge_distances.append((0 - attach[1]) / direction_y)
            elif direction_y > 0:
                edge_distances.append((height - attach[1]) / direction_y)
            distance = min(edge_distances)
            endpoint = (
                round(attach[0] + direction_x * distance),
                round(attach[1] + direction_y * distance),
            )
            branches.append([attach, endpoint])
        volcano_center = (center_x, center_y)
        lava_radii = (lake_radius_x, lake_radius_y)
    else:
        path, branches = _route_paths(rng, waypoint_count, layout, map_size, branch_count)
    paths = [path, *branches]
    path_width = CELL_SIZE * corridor_width
    styles = {
        "Höhle": ("#343a3d", "#a0a9a5", "#24282a", "#746e5f", "#8c8069", "#6ba6a2", "#b8e4d8"),
        "Eishöhle": ("#b8dce8", "#547b8a", "#537f91", "#d8f3fa", "#8bc9df", "#91dff2", "#f2fdff"),
        "Vulkanhöhle": ("#382c2a", "#b77043", "#241d1c", "#71605a", "#f27a35", "#ed572d", "#ffc06c"),
        "Pflanzenhöhle": ("#344b38", "#a9bd7a", "#1c3328", "#82704c", "#8aa75c", "#78a94e", "#c2d881"),
    }
    background, grid_color, path_edge, path_color, dash_color, feature_fill, feature_stroke = styles[variant]

    rocks = []
    for _ in range(48):
        x = rng.randint(20, width - 20)
        y = rng.randint(20, height - 20)
        if volcano_center and lava_radii:
            center_x, center_y = volcano_center
            radius_x, radius_y = lava_radii
            if ((x - center_x) / radius_x) ** 2 + ((y - center_y) / radius_y) ** 2 < 1:
                continue
        if any(_distance_to_path((x, y), route) < path_width / 2 + 24 for route in paths):
            continue
        radius = rng.randint(8, 24)
        rocks.append(
            f'<ellipse cx="{x}" cy="{y}" rx="{radius + 8}" ry="{radius}" '
            'fill="#262a2c" stroke="#55595a" stroke-width="3" />'
        )

    crystals = []
    for _ in range(12):
        x = rng.randint(35, width - 35)
        y = rng.randint(35, height - 35)
        if volcano_center and lava_radii:
            center_x, center_y = volcano_center
            radius_x, radius_y = lava_radii
            if ((x - center_x) / radius_x) ** 2 + ((y - center_y) / radius_y) ** 2 < 1:
                continue
        if any(_distance_to_path((x, y), route) < path_width / 2 + 10 for route in paths):
            continue
        feature_class = f'cave-feature {variant.lower()}-feature'
        if variant == "Vulkanhöhle":
            feature = (
                f'<path class="{feature_class}" '
                f'd="M {x} {y + 13} L {x + 4} {y - 7} L {x + 9} {y + 4} '
                f'L {x + 14} {y - 13} L {x + 20} {y + 13} Z" '
                f'fill="{feature_fill}" stroke="{feature_stroke}" stroke-width="3" />'
            )
        elif variant == "Pflanzenhöhle":
            feature = (
                f'<path class="{feature_class}" '
                f'd="M {x + 7} {y + 14} Q {x - 8} {y - 2} {x + 5} {y - 9} '
                f'Q {x + 13} {y - 1} {x + 7} {y + 14} '
                f'M {x + 8} {y + 14} Q {x + 3} {y - 7} {x + 20} {y - 11} '
                f'Q {x + 22} {y + 2} {x + 8} {y + 14} Z" '
                f'fill="{feature_fill}" stroke="{feature_stroke}" stroke-width="2" />'
            )
        else:
            feature = (
                f'<path class="{feature_class}" '
                f'd="M {x} {y + 13} L {x + 8} {y - 8} '
                f'L {x + 15} {y + 13} Z" fill="{feature_fill}" '
                f'stroke="{feature_stroke}" stroke-width="2" />'
            )
        crystals.append(feature)

    volcanoes = []
    lava_lake = ""
    if volcano_center and lava_radii:
        center_x, center_y = volcano_center
        radius_x, radius_y = lava_radii
        lava_lake = (
            f'<ellipse class="volcano-lake" cx="{center_x}" cy="{center_y}" '
            f'rx="{radius_x}" ry="{radius_y}" fill="#b8321d" '
            'stroke="#ff9b3d" stroke-width="12" />'
            f'<ellipse cx="{center_x}" cy="{center_y}" '
            f'rx="{radius_x * 0.78:.1f}" ry="{radius_y * 0.72:.1f}" '
            'fill="#f06424" opacity="0.92" />'
            f'<path d="M {center_x - radius_x * 0.58:.1f} {center_y - radius_y * 0.12:.1f} '
            f'Q {center_x - radius_x * 0.08:.1f} {center_y - radius_y * 0.55:.1f} '
            f'{center_x + radius_x * 0.10:.1f} {center_y - radius_y * 0.08:.1f} '
            f'Q {center_x + radius_x * 0.35:.1f} {center_y + radius_y * 0.20:.1f} '
            f'{center_x + radius_x * 0.62:.1f} {center_y + radius_y * 0.05:.1f}" '
            'fill="none" stroke="#ffc45b" stroke-width="8" stroke-linecap="round" />'
        )
        volcano_size = max(18, round(min(width, height) * 0.075))
        inset = volcano_size * 1.4
        volcano_x, volcano_y = rng.choice((
            (inset, inset),
            (width - inset, inset),
            (inset, height - inset),
            (width - inset, height - inset),
        ))
        volcanoes.append(
            f'<g class="volcano-cone" transform="translate({volcano_x:.1f} {volcano_y:.1f})">'
            f'<path d="M {-volcano_size} {volcano_size} L {-volcano_size * 0.28} {-volcano_size} '
            f'L {volcano_size} {volcano_size} Z" fill="#292321" stroke="#100f0e" stroke-width="5" />'
            f'<path d="M {-volcano_size * 0.62} {volcano_size * 0.28} '
            f'L {-volcano_size * 0.20} {-volcano_size * 0.48} '
            f'L {volcano_size * 0.62} {volcano_size * 0.28} Z" fill="#514039" />'
            f'<path d="M {-volcano_size * 0.28} {-volcano_size} '
            f'L {-volcano_size * 0.03} {-volcano_size * 0.70} '
            f'L {volcano_size * 0.24} {-volcano_size}" fill="#ef5729" stroke="#ffb34e" stroke-width="4" />'
            f'<ellipse cx="{-volcano_size * 0.28:.1f}" cy="{-volcano_size * 0.88:.1f}" '
            f'rx="{volcano_size * 0.22:.1f}" ry="{volcano_size * 0.08:.1f}" '
            'fill="#ff8a30" stroke="#ffc45b" stroke-width="3" />'
            '</g>'
        )

    return (
        f'<rect width="{width}" height="{height}" fill="{background}" />'
        + _grid(grid_color, map_size, 0.16)
        + lava_lake
        + _path_svg(paths, path_edge, path_width + 30)
        + _path_svg(paths, path_color, path_width)
        + "".join(
            f'<polyline points="{_polyline(route)}" fill="none" stroke="{dash_color}" '
            'stroke-width="4" stroke-dasharray="3 14" stroke-linecap="round" />'
            for route in paths
        )
        + "".join(rocks)
        + "".join(crystals)
        + "".join(volcanoes),
        [],
        path,
    )


def _ice_cave(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    return _cave(
        rng, waypoint_count, layout, map_size, branch_count, room_shape,
        corridor_width, "Eishöhle",
    )


def _volcano_cave(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    return _cave(
        rng, waypoint_count, layout, map_size, branch_count, room_shape,
        corridor_width, "Vulkanhöhle",
    )


def _plant_cave(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    return _cave(
        rng, waypoint_count, layout, map_size, branch_count, room_shape,
        corridor_width, "Pflanzenhöhle",
    )


def _ruins(
    rng: random.Random,
    waypoint_count: int,
    layout: str,
    map_size: tuple[int, int],
    branch_count: int,
    room_shape: str,
    corridor_width: int,
) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    # Baut Ruinen mit Wegen und alten Mauerstücken.
    del room_shape
    width, height = map_size
    path, branches = _route_paths(rng, waypoint_count, layout, map_size, branch_count)
    paths = [path, *branches]
    path_width = CELL_SIZE * corridor_width

    walls = []
    for _ in range(40):
        x = rng.randrange(20, width - 70, CELL_SIZE)
        y = rng.randrange(20, height - 60, CELL_SIZE)
        if any(
            _distance_to_path((x + CELL_SIZE, y + CELL_SIZE), route) < path_width / 2 + 25
            for route in paths
        ):
            continue
        wall_width = rng.choice((CELL_SIZE, CELL_SIZE * 2, CELL_SIZE * 3))
        wall_height = rng.choice((CELL_SIZE // 2, CELL_SIZE, CELL_SIZE * 2))
        walls.append(
            f'<rect x="{x}" y="{y}" width="{wall_width}" height="{wall_height}" '
            'fill="#81765e" stroke="#514d40" stroke-width="5" />'
            f'<path d="M {x + 8} {y + 8} h {max(8, wall_width - 16)}" '
            'stroke="#a69a79" stroke-width="3" />'
        )

    return (
        f'<rect width="{width}" height="{height}" fill="#b9a67d" />'
        + _grid("#615e4c", map_size, 0.25)
        + _path_svg(paths, "#9b895f", path_width + 16)
        + _path_svg(paths, "#d1bc8e", path_width)
        + "".join(walls),
        [],
        path,
    )


_MAP_BUILDERS: dict[str, MapBuilder] = {
    "Verlies": _dungeon,
    "Wald": _forest,
    "Höhle": _cave,
    "Eishöhle": _ice_cave,
    "Vulkanhöhle": _volcano_cave,
    "Pflanzenhöhle": _plant_cave,
    "Ruinen": _ruins,
}


# Diese Hauptfunktion baut alle acht Karten mit den gewählten Einstellungen.
def generate_maps(
    rng: random.Random | None = None,
    layout: str = "Zufällig",
    room_count: int = 5,
    chunk_size: tuple[int, int] = DEFAULT_CHUNK_SIZE,
    theme: str = "Alle",
    room_shape: str = "Gemischt",
    branch_count: int = 2,
    corridor_width: int = 1,
    include_encounter_points: bool = False,
) -> list[dict[str, object]]:
    """Create eight randomized maps across four encounter scenes."""
    generator = rng or random.Random()
    if layout not in {"Zufällig", "Kreuzung"}:
        raise ValueError(f"Unbekannte Wegeführung: {layout}")
    if not 3 <= room_count <= 10:
        raise ValueError("Die Raum- oder Wegpunktzahl muss zwischen 3 und 10 liegen.")
    if chunk_size not in CHUNK_SIZE_OPTIONS:
        raise ValueError(f"Unbekannte Kartengröße in Chunks: {chunk_size}")
    if theme not in {"Alle", *_MAP_BUILDERS}:
        raise ValueError(f"Unbekanntes Thema: {theme}")
    if room_shape not in {"Eckig", "Organisch", "Gemischt"}:
        raise ValueError(f"Unbekannte Raumform: {room_shape}")
    if not 0 <= branch_count <= 4:
        raise ValueError("Die Zahl der zusätzlichen Abzweigungen muss zwischen 0 und 4 liegen.")
    if corridor_width not in {1, 2, 3}:
        raise ValueError("Die Wegbreite muss zwischen 1 und 3 Rasterfeldern liegen.")
    map_size = (chunk_size[0] * CELL_SIZE, chunk_size[1] * CELL_SIZE)
    if theme == "Alle":
        themes = list(_MAP_BUILDERS) * (MAP_OPTION_COUNT // len(_MAP_BUILDERS))
        remaining_count = MAP_OPTION_COUNT - len(themes)
        themes.extend(generator.sample(list(_MAP_BUILDERS), remaining_count))
    else:
        themes = [theme] * MAP_OPTION_COUNT
    generator.shuffle(themes)
    maps = []
    for theme in themes:
        title = generator.choice(MAP_NAMES[theme])
        selected_layout = (
            generator.choice(("Kurvig", "Kreuzung"))
            if layout == "Zufällig"
            else layout
        )
        content, rooms, route = _MAP_BUILDERS[theme](
            generator,
            room_count,
            selected_layout,
            map_size,
            branch_count,
            room_shape,
            corridor_width,
        )
        encounter_points: list[dict[str, int | str]] = []
        if include_encounter_points:
            marker_svg, encounter_points = _encounter_marker_svg(route, map_size)
            content += marker_svg
        safe_title = html.escape(title)
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {map_size[0]} {map_size[1]}" role="img" '
            f'data-layout="{selected_layout}" '
            f'data-theme="{theme}" '
            f'data-corridor-width="{corridor_width}" '
            f'data-encounter-points="{str(include_encounter_points).lower()}" '
            f'data-chunks="{chunk_size[0]}x{chunk_size[1]}" '
            f'aria-label="{safe_title}">'
            + content
            + "</svg>"
        )
        maps.append(
            {
                "theme": theme,
                "title": title,
                "description": MAP_DESCRIPTIONS[theme],
                "layout": selected_layout,
                "rooms": rooms,
                "encounter_points": encounter_points,
                "svg": svg,
            }
        )
    return maps
