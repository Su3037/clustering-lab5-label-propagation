# 视频与课件的复现

## 视频

运行需求：Node.js 20+、Python 3.10+、Pillow、NumPy、FFmpeg。macOS默认使用系统黑体和宋体，不分发字体文件。Linux可安装Noto CJK字体，或通过 `CLUSTER_SANS_FONT` 与 `CLUSTER_SERIF_FONT` 指定有使用权的字体路径。

```sh
python3 -m pip install Pillow numpy
node scripts/build-traces.mjs
python3 scripts/render_film.py --preview
python3 scripts/render_film.py
python3 scripts/compose_score.py
ffmpeg -ss 53 -i site/media/neighbors.mp4 -t 87 -c:v libx264 -preset fast -crf 21 -c:a aac -b:a 160k -movflags +faststart site/media/one-graph.mp4
```

`render_film.py`把视频做成确定性时间函数，每帧由时间与真实算法记录计算。`--preview`生成12秒样片和全部分镜静帧，`--stills`只生成静帧。完整视频为1920×1080、30fps、229秒，使用H.264与AAC。

`video/storyboard.json`是分镜、时长与字幕的主来源。运行脚本会生成文字稿、VTT、封面与章节表。字幕已烧录在画面中，VTT用于可选独立字幕。视频没有旁白。

配乐由 `compose_score.py` 使用合成器音色、原创分解和弦与事件音产生。节点改变的音符与字幕结论出现在相同时刻。没有网络音乐采样或收费生成API。

替换为自己有权使用的音乐：`python3 scripts/compose_score.py --music /path/to/your-audio.mp3`。替换后应相应更新来源与许可说明。不要把网上能播放等同于可以再分发。

## 可编辑课件

`site/downloads/label-propagation.pptx`的文字、图节点、连线和5张表格均为可编辑对象，封面引用本项目原创视频的一帧。无需重建就可以在PowerPoint等应用中修改。源工程是 `scripts/build_deck.mjs`。

本次构建使用Codex内置的 `@oai/artifact-tool` 2.8.99；这是实际使用环境，不假定它可以通过公共npm安装。脚本通过环境变量读取技能目录、Python与Node依赖位置。若有相同运行环境，可执行：

```sh
PRESENTATION_SKILL_DIR=/path/to/presentations/skill \
RUNTIME_PYTHON=/path/to/python3 \
RUNTIME_NODE=/path/to/node \
RUNTIME_NODE_MODULES=/path/to/node_modules \
node scripts/build_deck.mjs
```

在项目根目录链接相应 `node_modules` 后运行。构建器先渲染，再检查PPTX结构、尺寸、字体声明、原生表格和重新导入。最终目标文件已存在时，改用新文件名生成修订版，避免覆盖审阅稿。

工具的直接PDF导出缺少内置字体资源，因此本项目使用ReportLab把同一批渲染页包装成PDF预览。PDF不是编辑源文件，编辑请使用PPTX。网页预览也来自这批渲染页，并提供每页备注。

## 打包下载材料

```sh
python3 -m pip install reportlab
python3 scripts/package_materials.py
```

该步骤复制讲义、练习、备注、独立Python实现和样例JSON到网站下载区。习题正文由 `site/questions.js` 单一来源生成。静态站点的日常部署不重新渲染视频或PPT，直接发布已验证的文件。

## 数据一致性

JS引擎 `site/algorithm.js` 独立实现LP；`build-traces.mjs`运行它后产生 `data/traces.json`，视频与课件读取同一份推演记录。Python实现使用另一份逻辑，与JS交叉核对。图的结构与权重引用教师小图并标注来源，未分发教师原课件和视频。
