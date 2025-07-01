from django.test import TestCase
from core import *

class ColorHarmonyTests(TestCase):

    def test_complementary(self):
        self.assertTrue(is_complementary(0, 180))
        self.assertTrue(is_complementary(30, 210))
        self.assertFalse(is_complementary(0, 160))

    def test_analogous(self):
        self.assertTrue(is_analogous(30, 50))
        self.assertTrue(is_analogous(350, 10))
        self.assertFalse(is_analogous(0, 90))

    def test_triadic(self):
        self.assertTrue(is_triadic(0, 120))
        self.assertTrue(is_triadic(0, 240))
        self.assertFalse(is_triadic(0, 90))

    def test_monochromatic(self):
        self.assertTrue(is_monochromatic(30, 33, 50, 55, 60, 62))    # within tolerance
        self.assertFalse(is_monochromatic(30, 90, 50, 80, 60, 20))   # outside range
