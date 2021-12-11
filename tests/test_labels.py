import unittest
import math
from src.label.creator import create_3d_printer_label, IMG_WIDTH

MEMBER_ID = "1140"
MEMBER_NAME = "Firstname Lastname"


class TestLabels(unittest.TestCase):

    def test_3d_printer_label(self):
        expected_label_height_mm = 25
        expected_max_label_height_px = math.floor((expected_label_height_mm - 6) * 300 / 25.4) # Subtracting six accounts for the printer margins. 
        expected_label_width_px = IMG_WIDTH

        label = create_3d_printer_label(MEMBER_ID, MEMBER_NAME).generate_label()
        (label_width, label_height) = label.size

        self.assertAlmostEqual(expected_max_label_height_px, label_height, delta=5)
        self.assertEqual(expected_label_width_px, label_width)
