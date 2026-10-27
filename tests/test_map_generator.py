import random
import unittest
import xml.etree.ElementTree as ET

from map_generator import CHUNK_SIZE_OPTIONS, MAP_OPTION_COUNT, generate_maps


# Diese Proben schauen, ob der Kartenmacher richtig arbeitet.
class GenerateMapsTests(unittest.TestCase):
    # Es müssen acht lesbare Karten aus vier verschiedenen Orten entstehen.
    def test_generates_eight_valid_maps_across_four_scenes(self):
        maps = generate_maps(random.Random(12))

        self.assertEqual(len(maps), MAP_OPTION_COUNT)
        self.assertEqual(
            {map_data["theme"] for map_data in maps},
            {"Verlies", "Wald", "Höhle", "Ruinen"},
        )
        self.assertEqual(
            {theme: sum(map_data["theme"] == theme for map_data in maps)
             for theme in {"Verlies", "Wald", "Höhle", "Ruinen"}},
            {"Verlies": 2, "Wald": 2, "Höhle": 2, "Ruinen": 2},
        )
        for map_data in maps:
            root = ET.fromstring(map_data["svg"])
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertTrue(map_data["title"])
            self.assertTrue(map_data["description"])

    # Gleiche Zufallszahl bedeutet: Es kommen dieselben Karten heraus.
    def test_seed_produces_repeatable_maps(self):
        first = generate_maps(random.Random(27))
        second = generate_maps(random.Random(27))

        self.assertEqual(first, second)

    # Eine andere Zufallszahl soll andere Karten machen.
    def test_different_seeds_change_map_layouts(self):
        first = generate_maps(random.Random(1))
        second = generate_maps(random.Random(2))

        self.assertNotEqual(
            [map_data["svg"] for map_data in first],
            [map_data["svg"] for map_data in second],
        )

    # Bei der Kreuzungseinstellung sollen alle Karten eine Kreuzung haben.
    def test_cross_layout_is_applied_to_all_maps(self):
        maps = generate_maps(random.Random(8), layout="Kreuzung")

        self.assertEqual(len(maps), MAP_OPTION_COUNT)
        self.assertTrue(all(map_data["layout"] == "Kreuzung" for map_data in maps))
        self.assertTrue(
            all('data-layout="Kreuzung"' in map_data["svg"] for map_data in maps)
        )

    # Prüft, ob die gewünschte Zahl an Räumen wirklich da ist.
    def test_room_count_controls_number_of_dungeon_rooms(self):
        maps = generate_maps(random.Random(15), layout="Kreuzung", room_count=8)
        dungeon = next(map_data for map_data in maps if map_data["theme"] == "Verlies")
        root = ET.fromstring(dungeon["svg"])
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        self.assertEqual(len(dungeon["rooms"]), 8)
        self.assertEqual(
            len(root.findall(".//*[@class='dungeon-room']", namespace)),
            8,
        )

    # Nur Verliese bekommen Räume, die man direkt bearbeiten kann.
    def test_only_dungeon_maps_have_editable_rooms(self):
        maps = generate_maps(random.Random(34))

        for map_data in maps:
            if map_data["theme"] == "Verlies":
                self.assertTrue(map_data["rooms"])
            else:
                self.assertEqual(map_data["rooms"], [])

    # Ein ausgewählter Ort soll alle acht Karten füllen.
    def test_selected_theme_is_used_for_all_eight_maps(self):
        maps = generate_maps(random.Random(18), theme="Wald")

        self.assertEqual(len(maps), MAP_OPTION_COUNT)
        self.assertEqual({map_data["theme"] for map_data in maps}, {"Wald"})

    # Begegnungspunkte sollen nur erscheinen, wenn man sie einschaltet.
    def test_encounter_points_are_optional_and_follow_the_map_routes(self):
        maps_without_points = generate_maps(random.Random(21))
        self.assertTrue(all(not map_data["encounter_points"] for map_data in maps_without_points))
        self.assertTrue(
            all('data-encounter-points="false"' in map_data["svg"] for map_data in maps_without_points)
        )

        maps_with_points = generate_maps(random.Random(21), include_encounter_points=True)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        expected_types = {"start", "encounter", "danger", "treasure"}
        for map_data in maps_with_points:
            root = ET.fromstring(map_data["svg"])
            markers = root.findall(".//svg:g[@class='encounter-point']", namespace)

            self.assertEqual(
                {marker.get("data-encounter-point") for marker in markers},
                expected_types,
            )
            self.assertEqual(len(map_data["encounter_points"]), 4)
            self.assertTrue(
                all(point["id"].startswith("encounter-")
                    for point in map_data["encounter_points"])
            )
            self.assertTrue(
                all(0 <= point["x"] <= 1000 and 0 <= point["y"] <= 600
                    for point in map_data["encounter_points"])
            )

    # Ein kleines Verlies bekommt drei passende Punkte.
    def test_three_room_dungeon_uses_three_distinct_encounter_points(self):
        maps = generate_maps(
            random.Random(22),
            theme="Verlies",
            room_count=3,
            include_encounter_points=True,
        )

        for map_data in maps:
            self.assertEqual(
                [point["type"] for point in map_data["encounter_points"]],
                ["start", "encounter", "treasure"],
            )

    # Organische Räume sollen geschlossene Formen sein, die im Editor bleiben.
    def test_organic_rooms_are_closed_paths_and_remain_editable(self):
        maps = generate_maps(random.Random(18), theme="Verlies", room_shape="Organisch")

        for map_data in maps:
            root = ET.fromstring(map_data["svg"])
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            rooms = root.findall(".//svg:path[@class='dungeon-room']", namespace)

            self.assertEqual(len(rooms), len(map_data["rooms"]))
            self.assertTrue(all(room.get("d", "").endswith(" Z") for room in rooms))
            self.assertTrue(all("shape_points" in room for room in map_data["rooms"]))

    # Wegbreite und Abzweigungen sollen sich nach der Auswahl richten.
    def test_branch_count_and_corridor_width_are_applied(self):
        maps = generate_maps(
            random.Random(18),
            theme="Verlies",
            layout="Kreuzung",
            branch_count=3,
            corridor_width=2,
        )
        root = ET.fromstring(maps[0]["svg"])
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        branches = root.findall(
            ".//svg:path[@class='dungeon-corridor-branch']",
            namespace,
        )
        corridors = root.findall(
            ".//svg:path[@class='dungeon-corridor-main']",
            namespace,
        )

        self.assertEqual(len(branches), 5)
        self.assertTrue(all(path.get("stroke-width") == "80" for path in corridors))

    # Die gewählte Kartengröße soll auch im Raster zu sehen sein.
    def test_selected_chunk_size_sets_map_dimensions_and_grid(self):
        for chunk_size in CHUNK_SIZE_OPTIONS:
            with self.subTest(chunk_size=chunk_size):
                maps = generate_maps(random.Random(34), chunk_size=chunk_size)
                expected_width = chunk_size[0] * 40
                expected_height = chunk_size[1] * 40

                for map_data in maps:
                    self.assertIn(
                        f'viewBox="0 0 {expected_width} {expected_height}"',
                        map_data["svg"],
                    )
                    self.assertIn('class="map-grid"', map_data["svg"])
                    self.assertIn(
                        f'data-chunks="{chunk_size[0]}x{chunk_size[1]}"',
                        map_data["svg"],
                    )

    # Auch auf einer kleinen Karte müssen alle Räume Platz haben.
    def test_small_map_keeps_maximum_room_count_inside_bounds(self):
        maps = generate_maps(
            random.Random(12),
            room_count=10,
            chunk_size=(10, 10),
        )
        dungeon = next(map_data for map_data in maps if map_data["theme"] == "Verlies")

        self.assertEqual(len(dungeon["rooms"]), 10)
        for room in dungeon["rooms"]:
            self.assertGreaterEqual(room["x"], 0)
            self.assertGreaterEqual(room["y"], 0)
            self.assertLessEqual(room["x"] + room["width"], 400)
            self.assertLessEqual(room["y"] + room["height"], 400)

    # Falsche Einstellungen müssen abgelehnt werden.
    def test_invalid_layout_and_room_count_are_rejected(self):
        with self.assertRaises(ValueError):
            generate_maps(layout="Rundweg")
        with self.assertRaises(ValueError):
            generate_maps(room_count=11)
        with self.assertRaises(ValueError):
            generate_maps(chunk_size=(12, 12))
        with self.assertRaises(ValueError):
            generate_maps(theme="Sumpf")
        with self.assertRaises(ValueError):
            generate_maps(branch_count=5)
        with self.assertRaises(ValueError):
            generate_maps(corridor_width=4)


if __name__ == "__main__":
    unittest.main()
