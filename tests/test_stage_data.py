"""Validacao estrutural da primeira fase."""

import unittest

from game.world.stage_data import LEGACY_CODE_DUNGEON


class StageDataTests(unittest.TestCase):
    def test_exit_is_inside_stage(self):
        stage = LEGACY_CODE_DUNGEON
        self.assertGreater(stage.exit_x, stage.start[0])
        self.assertLessEqual(stage.exit_x, stage.width)

    def test_stage_has_required_content(self):
        stage = LEGACY_CODE_DUNGEON
        self.assertGreaterEqual(len(stage.platforms), 2)
        self.assertGreaterEqual(len(stage.enemies), 1)
        self.assertGreaterEqual(len(stage.items), 1)


if __name__ == "__main__":
    unittest.main()

