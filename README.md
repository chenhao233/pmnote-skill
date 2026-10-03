# PMNote Skill

[PMNote](https://pmnote.ai) 网站公开内容的 Markdown 索引，供 AI Agent 查找原文、回答游戏项目管理相关问题。

## 使用

把下面这句话发给你的 Agent：

> 帮我安装并启用 PMNote Skill：https://github.com/chenhao233/pmnote-skill

本仓库采用 [Agent Skills](https://agentskills.io/home) 格式。支持该格式的 Agent 可以将整个 `pmnote/` 文件夹安装到自己的技能目录，保留其中的 `references/`。

安装目录和备用方法见[安装说明](INSTALL.md)。装好后新开一个对话，用下面的问题试一下。

也可以直接把[内容索引](pmnote/references/index.md)交给 Agent 查阅。

可以这样问：

- 用 PMNote 帮我分析：版本快上线了，又有新需求插进来，该不该接？
- 用 PMNote 帮我看看：美术资产反复返工，应该先查哪里？
- 用 PMNote 帮我梳理：转岗游戏项目经理，需要补哪些能力？

## 内容

索引按文章、播客、术语、岗位、课程与咨询、指南和频道分类，保存标题与原文链接。Agent 根据问题查找相关内容，打开原文后作答，并附上出处。

- [SKILL.md](pmnote/SKILL.md)：Agent 的查阅说明
- [内容索引](pmnote/references/index.md)：全部分类入口

## 更新与反馈

更新已安装的 Skill，可以把这句话发给 Agent：

> 从 https://github.com/chenhao233/pmnote-skill 更新 PMNote Skill，并确认新对话可以使用。

Skill 会结合[网站当前目录](https://pmnote.ai/llms.txt)查找新内容。发现链接失效或使用问题，可以[提交 Issue](https://github.com/chenhao233/pmnote-skill/issues)。维护索引的方法见[维护说明](CONTRIBUTING.md)。

## 许可

仓库文件使用 [MIT License](LICENSE)。链接指向的文章、音视频等内容，版权归各自权利人。
