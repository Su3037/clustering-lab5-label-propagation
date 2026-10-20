# 圈子从哪里来 v4: script notes

Feedback on v3: the "neighbour's colours" story felt far-fetched, the algorithm part was too shallow, and the pacing
was too fast. v4 rebuilds the story around one everyday question and doubles the running time by playing the chosen
track twice at original speed (379.64 s). Timings and bilingual captions live in `video/storyboard-v4.json`; the
renderer is `scripts/render_film_v4.py` (it reuses the v3 scenes through time remapping).

## Arc

| Part | Time | What the viewer should take away |
|---|---|---|
| Cold open: 通讯录 | 0–34 | Grouping contacts by who keeps in touch is a real, familiar problem (community detection) |
| History | 34–51 | Raghavan, Albert & Kumara (2007): join the circle you are most connected to; real run on the contacts graph |
| Chip | 51–85 | The same problem inside every chip: EDA splits cells into blocks; long wires cost speed and power |
| Ruler and brute force | 85–119 | A ruler cuts 88 of 202; trying every split is hopeless (1.58 billion for 24 cells, a 477,121-digit count for a million) |
| The rule | 119–170 | Label propagation in one sentence, then the six questions it leaves open; a pause to think |
| Part two: nine layers | 190–343 | Labels → weighted vote → one update → a full round → stopping → sync vs async → cutsize → back to the chip → limits |
| Real-world use and ending | 343–379 | Clustering as coarsening before partitioning and placement; contacts = chip; "no one draws the circles" |

## Revisions

1. **Draft 1** opened on the chip and explained the rule once; it still felt like a lecture without a reason to care.
2. **Draft 2** moved the hook to the phone's contact list, which every viewer owns, and let the 2007 paper arrive as the
   answer to that question before the chip appears. The chip section now explains *why* the split matters (short vs
   long wires) before any algorithm.
3. **Draft 3** split the algorithm into nine numbered layers, each with one caption announcing it, so the depth is
   visible and the viewer always knows where they are. A full-screen "下篇" card lists the layers in the quiet bar
   between the two plays of the song.
4. **Draft 4** (pace): every caption gets about 4 s; the questions panel ends on "停在这里想一想" with several seconds of
   silence; brute-force counting got its own scene so the scale lands.

## Honesty checks

- The contacts graph (28 fictional people, 61 links) is generated deterministically in `scripts/build-film-v3.mjs`
  and replayed by `tests/film_v3_crosscheck.py` (3 rounds, cut 4, groups of 8/10/10).
- The gathered contact layout is drawn from the algorithm's result and says so on screen.
- The die and the short-vs-long wire scene are labelled as schematics; signal speed is only compared qualitatively.
- Partition counts: 24!/(8!³·3!) = 1,577,585,295; three-way splits of 10⁶ cells ≈ 3^10⁶/6, which has 477,121 digits.
- All other numbers come from the same engine runs as v3.
