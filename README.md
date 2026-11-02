# PMNote Skill

[PMNote](https://pmnote.ai) 网站公开内容的 Markdown 索引，供 AI Agent 查找原文、回答游戏项目管理相关问题。

个人学习、个人与团队工作、商业项目均可免费使用。无需因使用人数或工作用途另行付费。

## 使用

把下面这句话发给你的 Agent：

> 帮我安装并启用 PMNote Skill：https://github.com/chenhao233/pmnote-skill

本仓库采用 [Agent Skills](https://agentskills.io/home) 格式。支持该格式的 Agent 可以将整个 `pmnote/` 文件夹安装到自己的技能目录，保留其中的 `references/`。

安装目录和备用方法见[安装说明](INSTALL.md)。装好后新开一个对话，用下面的问题试一下。

也可以直接把[内容索引](pmnote/references/index.md)交给 Agent 查阅。

可以这样问：

- 帮我评估这个游戏版本临近上线的新需求，列出交付风险和需要确认的条件。
- 美术资产反复返工，请结合已有材料排查流程问题，给出下一步。
- 用 PMNote 帮我梳理：学习游戏项目管理，需要掌握哪些基础知识？

## 内容

索引按文章、播客、术语、岗位、课程与咨询、指南、频道、面经与游戏研发 AI 工具分类，保存标题与原文链接。面经通过随包只读脚本读取当前匿名公开正文，保留分享人署名。Agent 根据问题查找相关内容，打开原文后作答，并附上出处。

- [SKILL.md](pmnote/SKILL.md)：Agent 的查阅说明
- [内容索引](pmnote/references/index.md)：全部分类入口

## 更新与反馈

更新已安装的 Skill，可以把这句话发给 Agent：

> 从 https://github.com/chenhao233/pmnote-skill 更新 PMNote Skill，并确认新对话可以使用。

Skill 会结合[网站当前目录](https://pmnote.ai/llms.txt)查找新内容。发现链接失效或使用问题，可以[提交 Issue](https://github.com/chenhao233/pmnote-skill/issues)。维护索引的方法见[维护说明](CONTRIBUTING.md)。

## 许可

采用[免费使用许可](LICENSE)，允许个人及团队工作、商业项目与内部适配；公开再分发、转售Skill或对外打包分发等另行授权。文章、音视频和课程正文的版权与访问权限各自独立。

这是公开提供的 Skill，不是开源项目。GitHub 站内查看和 Fork 按平台规则执行；旧版 v1.0.0 的 MIT 授权不因新许可自动撤销。
