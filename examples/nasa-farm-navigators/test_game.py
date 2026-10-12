import json
from pathlib import Path
import subprocess
import sys
import unittest
from copy import deepcopy
from itertools import product

sys.path.insert(0, str(Path(__file__).resolve().parent))
from farm_game import start, play


class GameTests(unittest.TestCase):
    def test_all_crop_and_action_combinations_have_explained_final_states(self):
        for crop, water_cost in [('drought_tolerant', 1), ('water_demanding', 2)]:
            for actions in product(('irrigate', 'conserve'), repeat=2):
                with self.subTest(crop=crop, actions=actions):
                    initial = start(crop)
                    original = deepcopy(initial)
                    result = play(play(initial, actions[0]), actions[1])
                    irrigations = actions.count('irrigate')
                    self.assertEqual(initial, original)
                    self.assertEqual(result['status'], 'complete')
                    self.assertEqual(result['turn'], 2)
                    self.assertEqual(len(result['history']), 2)
                    self.assertEqual(result['water_units'], 4 - water_cost * irrigations)
                    self.assertEqual(result['budget_units'], 3 - irrigations)
                    self.assertEqual(result['learning_points'],
                                     int(actions[0] == 'irrigate') + int(actions[1] == 'conserve'))
                    for turn, entry in enumerate(result['history']):
                        self.assertIn(actions[turn], entry['explanation'])
                        self.assertIn(crop, entry['explanation'])
                        self.assertIn(entry['synthetic_weather'], entry['explanation'])
                        self.assertIn('교육용 규칙', entry['explanation'])
                    self.assertIn('실제 농업 측정값이나 수확량 예측이 아닙니다', result['summary'])
                    self.assertIn(f"{result['learning_points']}/2", result['summary'])

    def test_two_turn_choices_change_resources_and_finish(self):
        result = play(play(start('drought_tolerant'), 'irrigate'), 'conserve')
        self.assertEqual(result['status'], 'complete')
        self.assertEqual((result['water_units'], result['budget_units'], result['learning_points']), (3, 2, 2))
        self.assertEqual(len(result['history']), 2)
        self.assertEqual(result['history'][0]['resource']['source_id'], 'official-challenge')
        with self.assertRaises(ValueError):
            play(result, 'conserve')

    def test_crop_choice_and_invalid_action_do_not_mutate_input(self):
        state = start('water_demanding')
        original = deepcopy(state)
        with self.assertRaises(ValueError):
            play(state, 'buy')
        self.assertEqual(state, original)
        result = play(state, 'irrigate')
        self.assertEqual(result['water_units'], 2)
        self.assertEqual(state, original)
        state['water_units'] = 0
        with self.assertRaises(ValueError):
            play(state, 'irrigate')

    def test_actual_cli_plays_and_discloses_synthetic_data(self):
        output = subprocess.run([sys.executable, str(Path(__file__).with_name('farm_game.py')),
                                 '--crop', 'water_demanding', '--actions', 'conserve', 'irrigate'],
                                text=True, capture_output=True, check=True)
        result = json.loads(output.stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['learning_points'], 0)
        self.assertIn('no NASA observations', result['disclosure'])


if __name__ == '__main__':
    unittest.main()
