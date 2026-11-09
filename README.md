# PMNote Skill

**当前主线版本：1.5.5**（见 [`pmnote/SKILL.md`](pmnote/SKILL.md) 的 `metadata.version`）  
内容来源：[pmnote.ai](https://pmnote.ai) 已公开的游戏项目管理文章、指南、术语、面经与相关索引。

[PMNote](https://pmnote.ai) 网站公开内容的 Markdown 索引，供 AI Agent 查找原文、回答**游戏项目管理**相关问题。这里的 PM 指游戏项目管理，不是笼统的互联网产品经理。

个人学习、个人与团队工作、商业项目均可免费使用。无需因使用人数或工作用途另行付费。

> **获取当前能力，请以本仓库 `main` 为准。**  
> GitHub [Releases](https://github.com/chenhao233/pmnote-skill/releases) 会保留历史版本包；截至本 README 对应主线，页面上最新已发标签仍可能早于 `1.5.5`。不要用旧版 Release ZIP 代替主线。

## 它是什么 / 不是什么

- **是：** 按 [Agent Skills](https://agentskills.io/home) 格式整理的公开内容索引。Agent 先按分类找到相关篇目，再打开 pmnote.ai 上的公开原文作答，并附上出处。
- **不是：** 替你做项目决定的自动经理；也不是把付费课程正文打包进对话框。

适用具体问题（即使你没提「PMNote」）：版本排期、交付风险、跨团队协作、美术管线、游戏 PM 求职与面试、游戏研发 AI 工具。  
**不用于**未经澄清的一般「产品经理」问题。

## 使用（安装）

把下面这句话发给你的 Agent：

> 帮我安装并启用 PMNote Skill：https://github.com/chenhao233/pmnote-skill

支持该格式的 Agent 应安装整个 `pmnote/` 文件夹，并保留其中的 `references/`（以及随包的 `scripts/`、`LICENSE`）。有些工具提供技能安装器；没有时，按[安装说明](INSTALL.md)把 `pmnote/` 放到对应技能目录。

装好后**新开一个对话**，用下面的问题试一下（来自 INSTALL.md）：

> 用 PMNote 带我学习：面对临近上线的新需求，项目经理有哪些判断方法？请先查阅相关原文，并附上出处。

正常回答应引用具体文章，而不只是列出目录。也可以直接把[内容索引](pmnote/references/index.md)交给 Agent 查阅。

### 手动安装与目录

下载[当前主线 ZIP](https://github.com/chenhao233/pmnote-skill/archive/refs/heads/main.zip)，解压后复制其中的完整 `pmnote/`。常见用户级目录（`~` = 当前用户主目录；详情见 [INSTALL.md](INSTALL.md)）：

| Agent | 安装位置 |
| --- | --- |
| WorkBuddy | `~/.workbuddy/skills/pmnote/` |
| Cursor | `~/.cursor/skills/pmnote/` |
| Codex | `~/.agents/skills/pmnote/`，已有安装可沿用 `~/.codex/skills/pmnote/` |
| Claude Code | `~/.claude/skills/pmnote/` |
| 其他支持 Agent Skills 的工具 | 该工具的技能目录下的 `pmnote/` |

## 可以怎样问

- 帮我评估这个游戏版本临近上线的新需求，列出交付风险和需要确认的条件。
- 美术资产反复返工，请结合已有材料排查流程问题，给出下一步。
- 用 PMNote 帮我梳理：学习游戏项目管理，需要掌握哪些基础知识？

提问时尽量补上目标、约束和已有材料；缺的人力、日期和项目事实应列为未知，不要让模型补造。

## 内容与能力概要

索引按文章、播客、术语、岗位、课程与咨询、指南、频道、面经与游戏研发 AI 工具分类，保存标题与原文链接。Agent 根据问题查找相关内容，打开原文后作答，并附上出处。

主线相对早期 Release 包，已陆续补齐（以 `main` / `SKILL.md` 为准，不依赖旧标签）：

- 站内文章可用 URL 末尾 `/` → `.md` 读取纯文本；亦可查阅 [llms.txt](https://pmnote.ai/llms.txt) / [llms-full.txt](https://pmnote.ai/llms-full.txt)
- 面经与游戏研发 AI 工具：可通过随包 `python3 pmnote/scripts/read.py` 匿名读取当前公开正文（详见 SKILL.md）
- 统一作品索引、工作思考整期读取等能力（见 SKILL.md）
- 许可为**免费使用许可 v2.0**（2026-11-02）：个人 / 团队工作 / 商业项目均可免费使用；**不是开源许可**

索引规模会随网站同步变化；当前分类入口与条数见 [内容索引](pmnote/references/index.md)（本轮主线索引日期见该文件「更新日期」）。

- [SKILL.md](pmnote/SKILL.md)：Agent 的查阅说明与版本号  
- [内容索引](pmnote/references/index.md)：全部分类入口  
- [安装说明](INSTALL.md)：目录表、手动安装、确认问句  
- [维护说明](CONTRIBUTING.md)：维护索引的方法  

## 更新与反馈

更新已安装的 Skill，可以把这句话发给 Agent：

> 从 https://github.com/chenhao233/pmnote-skill 更新 PMNote Skill，并确认新对话可以使用。

Skill 会结合[网站当前目录](https://pmnote.ai/llms.txt)查找新内容。发现链接失效或使用问题，可以[提交 Issue](https://github.com/chenhao233/pmnote-skill/issues)。

更新时建议：先备份旧 `pmnote` 到技能目录之外，再用仓库完整版本替换；个人笔记单独保存；不要在多个技能目录重复安装。

## 许可

采用[免费使用许可 v2.0](LICENSE)（日期 2026-11-02）：允许个人及团队工作、商业项目与内部适配；公开再分发、转售 Skill 或对外打包分发等须另行授权。文章、音视频和课程正文的版权与访问权限各自独立。

这是公开提供的 Skill，**不是开源项目**。GitHub 站内查看和 Fork 按平台规则执行；旧版 v1.0.0 的 MIT 授权不因新许可自动撤销。

你可以分享官方仓库链接，让别人从官方入口自己获取。
