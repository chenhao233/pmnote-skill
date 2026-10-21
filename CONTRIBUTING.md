# 维护索引

本页供 PMNote 维护者更新和发布官方版本。使用问题请[提交 Issue](https://github.com/chenhao233/pmnote-skill/issues)；其他用途须按[许可](LICENSE)另行取得授权。

索引从 PMNote 已发布的公开目录生成。使用 Python 3.9 或更新版本，在仓库根目录运行：

```sh
python3 scripts/index.py update
python3 scripts/index.py check
git diff -- pmnote/references
```

`update` 只落盘标题、链接、面经公开署名和来源版本，不保存文章或面经正文。匿名面经列表可能随访问返回公开文字，脚本只输出索引字段；不使用账号Cookie、访问令牌或私有数据库。先核对差异，再提交发布。`check --remote` 会核对索引是否与当前网站一致；没有实质变化时不只为修改日期重写索引。

网页更新后，重新运行上述命令；用户已安装的文件通过重新安装或让 Agent 更新。日常查询也会使用网站当前目录查找新内容。

网站的正式部署入口已接入同一维护程序：上传前检查本仓库干净且主线已推送、候选目录可完整生成；部署后绑定实际生产SHA，更新、读正文及引用验证通过后才提交推送。新增栏目必须先确认静态目录或动态公开读取路径；只增加导航链接不等于正文可读。具体发布命令见网站仓库的 `docs/engineering/pmnote-skill-sync.md`。

可以独立运行真实验收，不写生产数据：

```sh
python3 scripts/index.py verify --expected-sha <build-info.json中的sha> --output /tmp/pmnote-skill-verification.json
python3 pmnote/scripts/read.py interviews --search 腾讯
python3 pmnote/scripts/read.py tool tripo
```

`verify` 核对当前目录没有遗漏，并将发现阶段的公开面经与单篇读取结果逐字比较，检查原文定位和署名；另读取AI工具实际正文。新增或改变读取逻辑后，还应在浏览器打开输出的原文链接检查定位。面经撤下不从本地历史恢复，来源不完整或大幅缩减时停止更新，不清空旧索引。

提交前运行 `python3 scripts/index.py check`。请使用 GitHub 的隐私邮箱提交；在 GitHub「Settings → Emails」可以找到自己的 `noreply` 地址。

本地可启用推送前检查：`git config core.hooksPath scripts/hooks`。检查会拦截含个人邮箱的提交；GitHub Actions 也会检查索引与打包。

发布安装包：

```sh
python3 scripts/index.py package --output /tmp/pmnote.zip
```

安装包包含 `pmnote/` 目录及许可证，上传到对应 GitHub Release。发布后用 ZIP 安装一次，并在新对话中确认能读原文、给出出处。
