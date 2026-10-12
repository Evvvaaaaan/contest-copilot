#!/usr/bin/env python3
"""Offline research catalog, not an agricultural game or decision model."""
import argparse
import json
from pathlib import Path


def search(query, catalog=None):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('A nonempty search query is required.')
    rows = json.loads(Path(catalog or Path(__file__).with_name('catalog.json')).read_text(encoding='utf-8'))
    words = query.casefold().split()
    ranked = []
    for row in rows:
        haystack = ' '.join([row['title'], row['summary'], *row['tags']]).casefold()
        score = sum(word in haystack for word in words)
        if score:
            ranked.append((score, row))
    ranked.sort(key=lambda item: (-item[0], item[1]['id']))
    return {'query': query.strip(), 'mode': 'offline_curated_metadata',
            'results': [dict(row, matching_terms=score) for score, row in ranked],
            'limitation': 'Metadata discovery only; no satellite observations, agronomic advice or educational outcome measured.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    args = parser.parse_args()
    try:
        print(json.dumps(search(args.query), indent=2))
    except ValueError as error:
        parser.error(str(error))
