# 当前状态

第四版短片《圈子从哪里来》、九层讲解、闯关实验、18 页课件与讲义已完成，并发布在 https://su3037.github.io/clustering-lab5-label-propagation/ 。

仓库 Su3037/clustering-lab5-label-propagation 保持 private；GitHub Pages 网站公开可访问，访问者可以观看含指定配乐的短片。网站由 GitHub Actions 在推送到 main 后测试并部署，实验在访客浏览器内运行，不依赖作者的电脑。

本地预览：`python3 scripts/serve.py`。

测试：`npm test`；`python3 tests/crosscheck.py`；`python3 tests/film_v3_crosscheck.py`；`python3 scripts/check_site.py`；`python3 tests/test_preview.py`。

重建：短片见 docs/REPRODUCE.md；课件 `python3 scripts/build_deck.py`；下载区 `python3 scripts/package_materials.py`。

历史版本的源文件仍在仓库中，对应关系见 video/README.md，网站与课件不再使用它们。

教师 Issue #4 尚未评论、未关闭，需要用户先审阅成果并另行确认。
