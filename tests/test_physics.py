"""Testes unitarios das formulas de movimento."""

import unittest

from game.systems.physics import approach, clamp, integrate


class PhysicsTests(unittest.TestCase):
    def test_approach_does_not_overshoot(self):
        self.assertEqual(approach(0, 10, 20), 10)
        self.assertEqual(approach(20, 10, 20), 10)

    def test_semi_implicit_euler(self):
        position, velocity = integrate(0, 10, 20, 0.5)
        self.assertEqual(velocity, 20)
        self.assertEqual(position, 10)

    def test_clamp(self):
        self.assertEqual(clamp(12, 0, 10), 10)
        self.assertEqual(clamp(-1, 0, 10), 0)


if __name__ == "__main__":
    unittest.main()

