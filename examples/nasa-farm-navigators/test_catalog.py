import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('farm_catalog', ROOT / 'catalog.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def test_every_catalog_entry_preserves_provenance_in_search(self):
        rows = json.loads((ROOT / 'catalog.json').read_text())
        sources = {row['id'] for row in json.loads((ROOT / 'research.json').read_text())['sources']}
        for row in rows:
            with self.subTest(resource=row['id']):
                self.assertEqual(row['source_id'], 'official-challenge')
                self.assertIn(row['source_id'], sources)
                self.assertTrue(row['locator'].strip())
                self.assertIn('linked product not inspected', row['inspection_scope'])
                url = urlparse(row['url'])
                self.assertEqual(url.scheme, 'https')
                self.assertIn(url.hostname, ('www.earthdata.nasa.gov', 'search.earthdata.nasa.gov'))
                returned = {item['id']: item for item in catalog.search(row['title'])['results']}[row['id']]
                for key, value in row.items():
                    self.assertEqual(returned[key], value)

    def test_irrigation_finds_relevant_official_resource(self):
        result = catalog.search('irrigation')
        self.assertEqual(result['results'][0]['id'], 'agriculture-water')
        self.assertTrue(result['results'][0]['url'].startswith('https://www.earthdata.nasa.gov/'))

    def test_vegetation_returns_traceable_metadata(self):
        results = catalog.search('vegetation')['results']
        self.assertTrue(results)
        sources = {x['id'] for x in json.loads((ROOT / 'research.json').read_text())['sources']}
        for row in results:
            self.assertIn(row['source_id'], sources)
            self.assertIn('Resources', row['locator'])

    def test_case_spacing_and_repeated_calls_are_deterministic(self):
        self.assertEqual(catalog.search('FLOODS')['results'], catalog.search('  floods  ')['results'])
        self.assertEqual(catalog.search('NASA'), catalog.search('NASA'))

    def test_no_match_returns_empty_and_blank_input_rejected(self):
        self.assertEqual(catalog.search('unobtainium')['results'], [])
        with self.assertRaises(ValueError):
            catalog.search('  ')

    def test_actual_cli_produces_parseable_disclosed_output(self):
        result = subprocess.run([sys.executable, str(ROOT / 'catalog.py'), 'soil moisture'],
                                capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        self.assertEqual(output['mode'], 'offline_curated_metadata')
        self.assertIn('no satellite observations', output['limitation'])
        self.assertTrue(output['results'])

    def test_official_scope_remains_distinct_from_internal_acceptance(self):
        contract = json.loads((ROOT / 'contract.json').read_text())
        self.assertTrue(all('prototype' in x['applicability'] for x in contract['conditions']))
        research = json.loads((ROOT / 'research.json').read_text())
        self.assertEqual(research['scenario_author'], 'assistant')
        self.assertFalse(research['official_submission_ready'])
        self.assertIn('educational game', research['official_scope'])


if __name__ == '__main__':
    unittest.main()
