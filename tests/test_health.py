"""Testes do componente reutilizavel de vida."""

import unittest

from game.components.health import Health


class HealthTests(unittest.TestCase):
    def test_damage_never_goes_below_zero(self):
        life = Health(5)
        self.assertTrue(life.damage(9))
        self.assertEqual(life.current, 0)
        self.assertTrue(life.empty)

    def test_healing_respects_maximum(self):
        life = Health(5, 2)
        self.assertTrue(life.heal(9))
        self.assertEqual(life.current, 5)

    def test_invalid_changes_are_ignored(self):
        life = Health(5)
        self.assertFalse(life.damage(0))
        self.assertFalse(life.heal(1))


if __name__ == "__main__":
    unittest.main()

