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
# Side runs used by the film, replayed independently.
G5 = [['A', 'B', 5], ['A', 'C', 1], ['B', 'C', 4], ['C', 'D', 2], ['D', 'E', 5], ['C', 'E', 1]]
assert solve('ABCDE', G5)['labels'] == d['golden']['labels'] and d['golden']['rounds'] == 2
rv = solve('ABCDE', G5, order='EDCBA'); assert rv['labels'] == d['reverse']['labels'] and rv['rounds'] == d['reverse']['rounds'] == 3
st = solve('ABCDE', [e if e[:2] != ['C', 'D'] else ['C', 'D', 10] for e in G5])
assert st['labels'] == d['strongCD']['labels'] and st['cut'] == d['strongCD']['metrics']['cut'] == 5
ps = solve('AB', [['A', 'B', 1]], mode='sync'); assert ps['status'] == d['pairSync']['status'] == 'cycle'
pa = solve('AB', [['A', 'B', 1]]); assert pa['labels'] == d['pairAsync']['labels'] == {'A': 'B', 'B': 'B'}
iso = solve('ABCDE', [['A', 'B', 3], ['C', 'D', 2]]); assert iso['labels']['E'] == 'E'
print('side runs ok: reverse', rv['rounds'], 'rounds; C-D=10 cut', st['cut'], '; sync pair', ps['status'])
# The contacts graph opening the v4 film, replayed independently.
s = d['social']; sg = s['graph']; sr = solve(sg['nodes'], sg['edges'])
assert sr['labels'] == s['run']['labels'] and sr['rounds'] == s['run']['rounds'] and sr['cut'] == s['run']['metrics']['cut']
print('contacts ok:', len(sg['nodes']), 'people', len(sg['edges']), 'links;', sr['rounds'], 'rounds; cut', sr['cut'],
      '; groups', sorted(len(v) for v in s['run']['metrics']['clusters'].values()))
