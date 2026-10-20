# 视频与课件的复现

## 第四版主片《圈子从哪里来》（当前网站默认）

379.64 秒，1920×1080、30 fps、H.264/AAC，中英双语字幕烧录在画面中，无配音。画面全部由 Pycairo 逐帧绘制（深色技术风格），需要 Python 3.10+、pycairo、Pillow、NumPy、FFmpeg 和 Noto Sans/Serif CJK SC 字体。

```sh
node scripts/build-film-v3.mjs                 # data/film-v3.json：24 单元电路、虚构通讯录与全部对照运行
python3 tests/film_v3_crosscheck.py            # 用独立 Python 实现复算短片中的每个数字
python3 scripts/render_film_v4.py --stills     # 每个场景一张关键帧，检查版面
python3 scripts/render_film_v4.py --start 0 --end 95     # 分段渲染无声画面（可并行）
python3 scripts/render_film_v4.py --start 95 --end 190
python3 scripts/render_film_v4.py --start 190 --end 285
python3 scripts/render_film_v4.py --start 285 --end 379.64
```

输出在 `build/private/film-v4/`（不入库），用 ffmpeg concat 拼接后得到无声画面。`video/storyboard-v4.json` 保存场景、章节与双语字幕；渲染器同时写出 `film-v4.zh.vtt`、`film-v4.en.vtt`、`chapters-v4.json` 和 `video/transcript-v4.md`。

配乐：指定音轨原速循环两遍，裁到 379.64 秒，音量 0.45，结尾 1.5 秒淡出，AAC 192k，视频流直接复制并 faststart。例如：

```sh
ffmpeg -i picture.mp4 -stream_loop 1 -i music.m4a -map 0:v -map 1:a -c:v copy \
  -af "atrim=0:379.64,volume=0.45,afade=t=out:st=378.14:d=1.5" -c:a aac -b:a 192k -movflags +faststart circles.mp4
```

网站与闯关使用的通讯录、电路图由 `node scripts/build-site-graphs.mjs` 导出到 `site/film-graphs.js`，`tests/site-quest.test.mjs` 检查它们与短片数据一致。剧本修改过程见 [第四版剧本说明](research/film-v4-script.md)。`scripts/render_film_v3.py` 是第三版（3 分 10 秒）的渲染器，第四版复用它的场景。

## 课件（PPTX、PDF 与网页预览）

```sh
python3 -m pip install python-pptx pycairo
python3 scripts/build_deck.py
```

`scripts/build_deck.py` 用一份页面描述生成三种输出：可编辑的 `site/downloads/label-propagation.pptx`（文字、节点、连线和表格都是原生对象，每页带讲解备注），矢量 `label-propagation.pdf`，以及 `site/slides/slide-NN.png` 网页预览。讲解备注同时写入 `presentation/notes.json` 与 `site/downloads/notes.json`。

18 页的顺序与短片一致：第 2–6 页对应上篇（通讯录、2007 年的办法、芯片、尺子与穷举、一条规则与六个问题），第 7–15 页对应下篇九层，第 16 页是现实中的用法，第 17 页课堂互动，第 18 页来源与许可。图上的标签、票数、轮数和 cutsize 都读自 `data/film-v3.json` 和 `site/film-graphs.js`，脚本开头会断言关键数字（通讯录 3 轮、cut 4；电路 5 轮、cut 2；尺子 88/202；老师的图 2 轮、cut 3）。

PDF 与预览图嵌入 Noto CJK 字形；PPTX 声明 PingFang SC 与 Songti SC，在 Windows 上会被替换为系统中文字体，版面以 PDF 为准。

## 打包下载材料

```sh
python3 scripts/package_materials.py
```

把第四版文字稿、九层讲义、来源、许可、独立 Python 实现和样例图复制到网站下载区，并从 `site/questions.js` 重新生成 `docs/EXERCISES.md` 与 `site/downloads/exercises.md`。日常部署不重新渲染视频或课件，直接发布已验证的文件。`python3 scripts/check_site.py` 会检查课件页数、备注一致，并确认网站、课件和文档里没有旧版短片的内容。

## 数据一致性

JS 引擎 `site/algorithm.js` 独立实现 LP；`scripts/build-film-v3.mjs` 运行它生成 `data/film-v3.json`，短片、课件、网站闯关读取同一份结果。Python 实现 `src/label_propagation.py` 使用另一份逻辑，`tests/crosscheck.py` 和 `tests/film_v3_crosscheck.py` 与 JS 交叉核对。图的结构与权重引用教师小图并标注来源，未分发教师原课件和视频。

## 历史版本

仓库保留前几版的源工程，便于追溯，但网站和课件只使用第四版。各文件的对应关系见 [video/README.md](../video/README.md)。

- 第三版（3 分 10 秒）：`scripts/render_film_v3.py`、`video/storyboard-v3.json`。第四版复用它的场景，所以渲染器仍需保留。
- 第二版（约 3 分 10 秒，34 个二维镜头）：`scripts/build-film-v2.mjs`、`plan_film_v2.py`、`render_film_v2.py`、`analyze_music.py`，数据 `data/film-v2.json`，测试 `tests/film-v2.test.mjs`。
- 第一版（229 秒，原创合成配乐）：`scripts/render_film.py`、`compose_score.py`、`video/storyboard.json`。网站上的 1 分 27 秒课堂慢速推演 `one-graph.mp4` 是第一版 53–140 秒的片段。
