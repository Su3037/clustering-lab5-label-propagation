#!/usr/bin/env python3
"""Replay data/film-v3.json with the independent Python implementation."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src'))
from label_propagation import solve
d = json.loads((ROOT / 'data/film-v3.json').read_text()); g = d['graph']
r = solve(g['nodes'], g['edges'])
labels = r['labels'] if isinstance(r, dict) else r[0]
assert labels == d['lp']['labels'], 'labels differ from the JS engine'
cut = lambda lab: sum(w for u, v, w in g['edges'] if lab[u] != lab[v])
assert cut(labels) == d['lp']['metrics']['cut'] and r['rounds'] == d['lp']['rounds']
assert cut(d['geometric']['labels']) == d['geometric']['metrics']['cut']
assert sorted(len([n for n in g['nodes'] if labels[n] == l]) for l in set(labels.values())) == [8, 8, 8]
c = next(e for e in d['golden']['events'] if e['node'] == 'C' and e['round'] == 1)
assert c['votes'] == {'B': 5, 'D': 2, 'E': 1} and c['label'] == 'B'
print('film-v3 ok: nodes', len(g['nodes']), 'edges', len(g['edges']), 'total', d['geometric']['metrics']['totalWeight'],
      'geometric cut', cut(d['geometric']['labels']), 'LP cut', cut(labels), 'rounds', d['lp']['rounds'])
