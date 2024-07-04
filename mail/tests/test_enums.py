import unittest

from mail.enums import UnitMapping


class UnitMappingTests(unittest.TestCase):
    def test_convert_code(self):
        data = [
            ("NAR", 30),
            ("GRM", 21),
            ("KGM", 23),
            ("MTK", 45),
            ("MTR", 57),
            ("LTR", 94),
            ("MTQ", 2),
            ("MLT", 74),
            ("ITG", 30),
            ("MGM", 111),
            ("TON", 25),
            ("MCG", 116),
            ("MCL", 110),
            ("MIM", 111),
            ("MCM", 116),
            ("MIR", 74),
            ("MCR", 110),
        ]

        for code, value in data:
            with self.subTest(code=code, value=value):
                self.assertEqual(value, UnitMapping[code].value)

    def test_convert_none(self):
        with self.assertRaises(KeyError):
            UnitMapping[None]

    def test_serializer_choices(self):
        choices = UnitMapping.serializer_choices()
        expected = [
            "NAR",
            "GRM",
            "KGM",
            "MTK",
            "MTR",
            "LTR",
            "MTQ",
            "MLT",
            "ITG",
            "MGM",
            "TON",
            "MCG",
            "MCL",
            "MIM",
            "MCM",
            "MIR",
            "MCR",
        ]

        self.assertEqual(choices, expected)
