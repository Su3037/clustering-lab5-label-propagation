# 邻居的颜色 v3: script notes

The user approved the dark technical look from the 45 s review cut and asked for a rewritten story with a fun hook,
real knowledge, and an ending that is worth thinking about outside chips. This file records how the script was built.
Captions and timings live in `video/storyboard-v3.json`; numbers in captions are filled from `data/film-v3.json`.

## Music map (from measured onsets, `video/music-cues-v2.json`)

| Time (s) | What the track does | What the film does there |
|---|---|---|
| 0 to 10.75 | sparse hits every ~2.13 s | cells land in three waves; the ruler drops on the 5.69 and 7.83 hits |
| 10.75 to 17.41 | no onsets at all | the punchline plays in silence: severed wires light up, the counter climbs |
| 17.41 | groove enters | the ruler's cuts break apart: "换个思路：不画线" |
| 32.03 to 34.17 | sixteenth-note drum roll | the title assembles one character per hit and locks on 34.17 |
| 49.06 to 51.18 | fill | weights land on the fill; D wins on its last hit |
| 63.15 | phrase accent | C commits B |
| 66.08 to 68.20 | fill | D and E update quickly; round 1 ends |
| 80.2 to 85.2 | phrase plus fill | synchronous pair flips label on each strong hit |
| 97.2 to 102.5 | thinner, a breath | the boundary moves when C–D becomes 10; the film breathes |
| 102.50 | re-entry | back to the 24 cells |
| 117.14 to 119.27 | fill | the three groups surface |
| 134.16 to 136.16 | fill | the rest of the chip-design pipeline lights up |
| 136.16 onward | softer outro | the reflective ending |
| 170.6 to 189.8 | sparse, then quiet | invitation to the lab and credits |

The onsets are spectral-flux estimates, not hand-annotated downbeats.

## Revisions

1. **Draft 1** followed the handoff's circuit direction: 24 cells, a geometric split, crossing edges, the rule, the payoff.
   It explained well but had no humour and no ending beyond "this is a clue for chip design".
2. **Draft 2** (structure). The geometric split became a person with a ruler: "多数人的第一反应：拿尺子，切两刀".
   The silent break in the track became the punchline ("也整齐地切断了…") plus one quick classroom image
   (按座位号分组：同桌拆散，好友隔三排), which is short, true to the picture, and not an extended analogy.
   The rule now has a clear identity/label split (名字是身份；标签是归属) because the ending needs it.
   The synchronous/asynchronous section became "同时说话会永远互换，轮流来才一致", which is accurate for the
   two-node example and easy to remember.
   The ending grows from three facts the film has shown: a node only sees its neighbours; its label is a weighted
   vote of its strongest connections; an isolated node keeps its own label forever. It closes on the ruler from the
   opening ("边界从来不是谁拿尺子画出来的，是一条条连接，自己长出来的") and one open question.
3. **Draft 3** (reading pace). Every caption was checked at about 6 Chinese characters per second or slower;
   lines over that were cut or given more time by borrowing from silent stretches. Long counts moved on screen
   (order strip, vote registers), so captions say only what the viewer should notice.

## Honesty checks

- The 24-cell graph is fictional and deterministic (`scripts/build-film-v3.mjs`); wires that would pass through a
  third cell are removed before any result is computed.
- The ruler partition is a separate comparison; label propagation starts from one label per cell, not from the ruler.
- "这里恰好 3 组，各 8 个" is stated as a property of this example; the teacher's graph (3 + 2) is shown next to it.
- Reverse visiting order is shown only for the teacher's graph, with its real 3 rounds and different label names.
- Strengthening C–D to 10 is a counterfactual run of the same engine; its cutsize is read from that run.
- The two-node synchronous run stops with status `cycle` after 2 rounds; the film says the state repeats rather than
  claiming more rounds were computed.
