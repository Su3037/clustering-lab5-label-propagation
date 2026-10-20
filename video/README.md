# 视频源文件

当前短片是第四版《圈子从哪里来》，6 分 20 秒（379.64 秒）。网站、课件和讲义都以它为准。

| 用途 | 当前（第四版） |
| --- | --- |
| 分镜、章节与双语字幕的来源 | `storyboard-v4.json` |
| 章节时间 | `chapters-v4.json` |
| 字幕 | `film-v4.zh.vtt`、`film-v4.en.vtt`（网站上的副本是 `site/media/circles.*.vtt`） |
| 文字稿 | `transcript-v4.md`（网站下载区的 `transcript.md`） |
| 渲染器 | `scripts/render_film_v4.py`（复用 `scripts/render_film_v3.py` 的场景） |
| 剧本说明 | `docs/research/film-v4-script.md` |

其余文件是历史版本，只为追溯和重建保留，内容已经过时：

- 第三版（“邻居的颜色”）：`storyboard-v3.json`、`chapters-v3.json`、`neighbors-v3.zh.vtt`、`transcript-v3.md`。第四版渲染器读取 `storyboard-v3.json` 里的场景，不能删除。
- 第二版：`storyboard-v2.json`、`music-cues-v2.json`、`transcript-v2.md`。
- 第一版：`storyboard.json`、`transcript.md`。网站上的课堂慢速推演 `one-graph.mp4` 来自第一版。
