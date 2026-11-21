import json
import pathlib
import unittest
import urllib.parse

from cartrack import vin

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "vpic_batch.json"   # a real vPIC answer, 2026-11-20


class Valid(unittest.TestCase):
    def test_a_real_vin_passes_its_check_digit(self):
        self.assertTrue(vin.valid("1HGCM82633A004352"))

    def test_one_wrong_character_fails(self):
        self.assertFalse(vin.valid("1HGCM82613A004352"))

    def test_a_check_digit_of_ten_is_written_x(self):
        self.assertTrue(vin.valid("1M8GDM9AXKP042788"))

    def test_letters_a_vin_never_uses_fail(self):
        self.assertFalse(vin.valid("1HGCM82633A00435O"))

    def test_wrong_length_fails(self):
        self.assertFalse(vin.valid("1HGCM82633A00435"))


class Decode(unittest.TestCase):
    def setUp(self):
        self.sent = []

    def post(self, url, body, headers=None):
        self.sent.append((url, urllib.parse.parse_qs(body.decode())))
        return FIXTURE.read_bytes()

    def test_returns_one_row_per_vin_from_the_real_answer(self):
        rows = vin.decode(["1HGCM82633A004352", "1HGCM82613A004352"], post=self.post)
        self.assertEqual(set(rows), {"1HGCM82633A004352", "1HGCM82613A004352"})
        self.assertEqual(rows["1HGCM82633A004352"]["Model"], "Accord")
        self.assertEqual(rows["1HGCM82613A004352"]["ErrorCode"], "1")

    def test_keeps_only_the_fields_that_have_a_value(self):
        row = vin.decode(["1HGCM82633A004352"], post=self.post)["1HGCM82633A004352"]
        self.assertNotIn("", row.values())
        self.assertNotIn("DriveType", row)

    def test_sends_vins_joined_by_semicolons_and_asks_for_json(self):
        vin.decode(["1HGCM82633A004352", "1HGCM82613A004352"], post=self.post)
        url, form = self.sent[0]
        self.assertTrue(url.endswith("/DecodeVINValuesBatch/"))
        self.assertEqual(form, {"DATA": ["1HGCM82633A004352;1HGCM82613A004352"], "format": ["json"]})

    def test_sends_at_most_50_vins_a_request(self):
        vin.decode([f"VIN{n:014d}" for n in range(120)], post=self.post)
        self.assertEqual([len(form["DATA"][0].split(";")) for _, form in self.sent], [50, 50, 20])

    def test_nothing_to_decode_sends_nothing(self):
        self.assertEqual(vin.decode([], post=self.post), {})
        self.assertEqual(self.sent, [])


class Identity(unittest.TestCase):
    def test_reads_the_real_accord(self):
        row = json.loads(FIXTURE.read_text(encoding="utf-8"))["Results"][0]
        self.assertEqual(vin.identity(row), {
            "year": 2003, "make": "honda", "model": "Accord", "trim": "EX-V6", "body": "coupe",
            "drive": None, "engine": "3.0l v6", "fuel": "gasoline", "transmission": "automatic",
        })

    def test_body_classes_map_to_the_catalogue_words(self):
        cases = {
            "Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)": "suv",
            "Pickup": "pickup",
            "Sedan/Saloon": "sedan",
            "Hatchback/Liftback/Notchback": "hatchback",
            "Minivan": "minivan",
            "Cargo Van": "van",
            "Convertible/Cabriolet": "convertible",
            "Wagon": "wagon",
            "Crossover Utility Vehicle (CUV)": "suv",
            "Trailer": None,
        }
        for body_class, body in cases.items():
            self.assertEqual(vin.identity({"BodyClass": body_class})["body"], body, body_class)

    def test_drive_types_map_to_the_catalogue_words(self):
        cases = {
            "4WD/4-Wheel Drive/4x4": "4wd",
            "AWD/All-Wheel Drive": "awd",
            "FWD/Front-Wheel Drive": "fwd",
            "RWD/Rear-Wheel Drive": "rwd",
            "4x2": "2wd",
        }
        for drive_type, drive in cases.items():
            self.assertEqual(vin.identity({"DriveType": drive_type})["drive"], drive, drive_type)

    def test_an_inline_engine_is_written_with_i(self):
        row = {"DisplacementL": "2.4", "EngineCylinders": "4", "EngineConfiguration": "In-Line"}
        self.assertEqual(vin.identity(row)["engine"], "2.4l i4")

    def test_an_empty_row_is_all_unknown(self):
        self.assertEqual(set(vin.identity({}).values()), {None})


if __name__ == "__main__":
    unittest.main()
