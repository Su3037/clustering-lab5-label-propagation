#!/usr/bin/env python3
"""Copy the current teaching materials into site/downloads and regenerate the exercise sheet.

Run after scripts/build_deck.py (which writes the PPTX, PDF, slide previews and notes).
  python3 scripts/package_materials.py
"""
from pathlib import Path
import shutil, json, subprocess
ROOT = Path(__file__).resolve().parents[1]; dest = ROOT / 'site/downloads'
assert (dest / 'label-propagation.pptx').exists() and (dest / 'label-propagation.pdf').exists(), 'Run scripts/build_deck.py first'

for src, name in [('video/transcript-v4.md', 'transcript.md'), ('src/label_propagation.py', 'label_propagation.py'),
                  ('docs/research/sources.md', 'sources.md'), ('docs/LEARN.md', 'learn.md'),
                  ('LICENSE', 'LICENSE.txt'), ('LICENSE-CONTENT.md', 'LICENSE-CONTENT.md'), ('THIRD_PARTY_NOTICES.md', 'THIRD_PARTY_NOTICES.md')]:
    shutil.copyfile(ROOT / src, dest / name)

g = json.loads((ROOT / 'data/traces.json').read_text())['graphs']['golden']
small = json.dumps({'nodes': g['nodes'], 'edges': g['edges']}, indent=2)
for p in [ROOT / 'data/golden.json', dest / 'golden.json']: p.write_text(small, encoding='utf-8')

module = "import{QUESTIONS}from './site/questions.js';console.log(JSON.stringify(QUESTIONS));"
q = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', module], cwd=ROOT, text=True))
lines = ['# 标签传播练习与解析', '', '对应短片《圈子从哪里来》和九层讲解。建议先在网页尝试，再阅读答案。', '']
for i, x in enumerate(q, 1):
    lines.extend([f'## {i} {x["q"]}', ''])
    lines.extend([f'- {chr(65 + j)}. {a}' for j, a in enumerate(x['a'])])
    lines.extend(['', f'答案：{chr(65 + x["correct"])}。{x["e"]}', ''])
for p in [ROOT / 'docs/EXERCISES.md', dest / 'exercises.md']: p.write_text('\n'.join(lines), encoding='utf-8')
print(f'Packaged transcript, learning notes, sources, licenses, golden graph and {len(q)} exercises')
