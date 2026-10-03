# 维护索引

本页供 PMNote 维护者更新和发布官方版本。使用问题请[提交 Issue](https://github.com/chenhao233/pmnote-skill/issues)；其他用途须按[许可](LICENSE)另行取得授权。

索引从 PMNote 已发布的公开目录生成。使用 Python 3.9 或更新版本，在仓库根目录运行：

```sh
python3 scripts/index.py update
python3 scripts/index.py check
git diff -- pmnote/references
```

`update` 只更新标题、链接和索引日期，不下载文章正文。先核对差异，再提交发布。`check --remote` 会核对索引是否与当前网站一致。

网页更新后，重新运行上述命令；用户已安装的文件通过重新安装或让 Agent 更新。日常查询也会使用网站当前目录查找新内容。

提交前运行 `python3 scripts/index.py check`。请使用 GitHub 的隐私邮箱提交；在 GitHub「Settings → Emails」可以找到自己的 `noreply` 地址。

本地可启用推送前检查：`git config core.hooksPath scripts/hooks`。检查会拦截含个人邮箱的提交；GitHub Actions 也会检查索引与打包。

发布安装包：

```sh
python3 scripts/index.py package --output /tmp/pmnote.zip
```

安装包包含 `pmnote/` 目录及许可证，上传到对应 GitHub Release。发布后用 ZIP 安装一次，并在新对话中确认能读原文、给出出处。
