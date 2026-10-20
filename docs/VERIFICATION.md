# 验证记录

日期：2026-10-20。对应第四版短片《圈子从哪里来》与配套网站、课件。

## 算法与数据

- `npm test`：13 项通过，包括引擎（教师 golden、异步/同步写回时刻、加权票数、平票、孤点、顺序与标签名、上限状态、输入验证），短片数据，以及网站闯关用图与答案。
- `tests/crosscheck.py`：Python 与 JS 两份独立实现，在 271 个固定种子的配置上逐节点比较票数、新旧标签、轮数、停止原因与加权割边，全部相符。
- `tests/film_v3_crosscheck.py`：用独立 Python 实现复算短片里的数字。通讯录 28 人、61 条联系，3 轮，cut 4，分组 8/10/10；24 单元电路标签传播 5 轮、cut 2，尺子切法 88/202。
- 教师 golden：正序异步、最小标签平票，B/B/B/E/E，2 轮，cutsize 3，3:2 分组；倒序 A/A/A/D/D，3 轮。

## 短片

- `site/media/circles.mp4`：379.64 秒，1920×1080，H.264 + AAC，faststart，44,347,523 字节，SHA-256 08cb4bd021298760a84d9dfc7dde2a8bf251d0f54d935699c48f03e0637aecad，与用户审定的成片一致。
- 中英字幕与章节由 `video/storyboard-v4.json` 生成；网页的章节按钮与九层讲解的跳转时间都在章节表内（`scripts/check_site.py`）。

## 课件

- `scripts/build_deck.py` 生成 18 页 PPTX（原生文字、节点、连线、表格与逐页备注）、矢量 PDF 和网页预览图；脚本开头断言关键数字与短片数据一致。
- PPTX 经 LibreOffice 重新打开并导出，18 页版面与 PDF 预览一致；尚未在 Microsoft PowerPoint 中复核，缺字体时可用 PDF。
- `scripts/check_site.py` 检查课件页数、备注与 PPTX 页数一致，并确认网站、课件、README 与 docs 中没有旧版短片的内容。

## 浏览器

- 网页课件 `slides.html` 可通过 `#页码` 直接打开某一页，End 键跳到第 18 页，无加载错误。
- 闯关、实验台和移动端的检查记录见合并的 PR #1。
- `tests/test_preview.py`：本地服务器的字节范围请求通过（章节跳转需要）。

## 部署

- GitHub Actions 在推送到 main 后运行上述测试与静态检查，成功后部署 `site/`。
- 仓库保持 private；网站公开可访问，含指定配乐的短片也可公开观看（用户已确认）。
- 未在教师 Issue 发表评论或关闭 Issue。
