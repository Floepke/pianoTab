import unittest
import sys, os

# Ensure project root on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from kivy.config import Config
# Use smaller window and multisampling off for tests
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'multisamples', '0')

from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock

from utils.canvas import Canvas


class DummyApp(App):
    def build(self):
        return Canvas(width_mm=210, height_mm=297)


class CanvasTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start a minimal Kivy App once for all tests
        cls.app = DummyApp()
        # Schedule stop right after build to avoid opening a window too long
        Clock.schedule_once(lambda dt: None, 0)
        # Build root widget without running full main loop
        cls.root = cls.app.build()

    def setUp(self):
        self.canvas = Canvas(width_mm=100, height_mm=100, background_color=(1,1,1,1))

    def test_add_rectangle(self):
        rid = self.canvas.add_rectangle(10, 10, 30, 30, fill=True, fill_color="#FF0000")
        self.assertIsInstance(rid, int)
        item = self.canvas.find_by_id(rid)
        self.assertIsNotNone(item)
        self.assertEqual(item['type'], 'rectangle')
        # Hit test inside
        self.assertTrue(self.canvas._hit_test(rid, (20, 20)))
        # Outside
        self.assertFalse(self.canvas._hit_test(rid, (5, 5)))

    def test_add_oval(self):
        oid = self.canvas.add_oval(40, 40, 60, 70, fill=True, fill_color="#00FF00")
        self.assertIsInstance(oid, int)
        item = self.canvas.find_by_id(oid)
        self.assertEqual(item['type'], 'oval')
        # Center should hit
        self.assertTrue(self.canvas._hit_test(oid, (50, 55)))
        # Far away should not
        self.assertFalse(self.canvas._hit_test(oid, (90, 90)))

    def test_add_line(self):
        lid = self.canvas.add_line(0, 0, 50, 0, color="#0000FF", width_mm=0.5)
        self.assertIsInstance(lid, int)
        item = self.canvas.find_by_id(lid)
        self.assertEqual(item['type'], 'line')
        # Hit near the line
        self.assertTrue(self.canvas._hit_test(lid, (25, 0.1)))
        # Far from the line
        self.assertFalse(self.canvas._hit_test(lid, (25, 5)))

    def test_add_polygon(self):
        pid = self.canvas.add_polygon([10,10, 30,10, 30,30, 10,30], fill=True, fill_color="#000000")
        self.assertIsInstance(pid, int)
        item = self.canvas.find_by_id(pid)
        self.assertEqual(item['type'], 'polygon')
        self.assertTrue(self.canvas._hit_test(pid, (20, 20)))
        self.assertFalse(self.canvas._hit_test(pid, (5, 5)))

    def test_tags_and_find(self):
        rid = self.canvas.add_rectangle(0,0,10,10, fill=True, fill_color="#FF0000", id=['note','selected'])
        self.canvas.add_tag(rid, 'visible')
        found = self.canvas.find_by_tag('note')
        self.assertIn(rid, found)
        self.canvas.remove_by_id(rid, 'selected')
        self.assertNotIn(rid, self.canvas.find_by_tag('selected'))

    def test_add_path(self):
        pid = self.canvas.add_path([0, 0, 50, 0, 50, 50], color="#123456", width_mm=0.3)
        self.assertIsInstance(pid, int)
        item = self.canvas.find_by_id(pid)
        self.assertEqual(item['type'], 'path')
        # Hits near first horizontal segment
        self.assertTrue(self.canvas._hit_test(pid, (25, 0.05)))
        # Hits near second vertical segment
        self.assertTrue(self.canvas._hit_test(pid, (50, 25)))
        # Miss
        self.assertFalse(self.canvas._hit_test(pid, (5, 5)))

    def test_add_path_input_validation(self):
        with self.assertRaises(ValueError):
            self.canvas.add_path([0, 0, 10])  # odd length

    def test_dash_options_are_stored_and_draw(self):
        lid = self.canvas.add_line(0, 0, 100, 0, color="#000000", width_mm=0.5, dash=True, dash_pattern_mm=(3, 1))
        item = self.canvas.find_by_id(lid)
        self.assertTrue(item['dash'])
        self.assertEqual(item['dash_mm'], (3.0, 1.0))
        # Also test with path
        pid = self.canvas.add_path([0,0, 0,50, 50,50], color="#000000", width_mm=0.5, dash=True, dash_pattern_mm=(2,2))
        pitem = self.canvas.find_by_id(pid)
        self.assertTrue(pitem['dash'])
        self.assertEqual(pitem['dash_mm'], (2.0, 2.0))


if __name__ == '__main__':
    unittest.main()
