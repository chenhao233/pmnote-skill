# 安装 PMNote Skill

安装内容是仓库中的整个 `pmnote/` 文件夹。`SKILL.md` 与 `references/` 放在一起，Agent 才能找到分类索引。

仅限个人学习使用；工作或商业用途需另行授权。安装时保留文件夹中的 `LICENSE`。

## 让 Agent 安装

> 帮我安装并启用 PMNote Skill：https://github.com/chenhao233/pmnote-skill

Agent 可以使用自身的技能安装器，或下载仓库后将 `pmnote/` 复制到技能目录。常见的用户级目录如下，`~` 表示当前用户的主目录：

| Agent | 安装位置 |
| --- | --- |
| WorkBuddy | `~/.workbuddy/skills/pmnote/` |
| Cursor | `~/.cursor/skills/pmnote/` |
| Codex | `~/.agents/skills/pmnote/`，已有安装可沿用 `~/.codex/skills/pmnote/` |
| Claude Code | `~/.claude/skills/pmnote/` |
| 其他支持 Agent Skills 的工具 | 该工具的技能目录下的 `pmnote/` |

更新时先找到已有的 `pmnote`，把旧版备份到技能目录之外，再用仓库中的完整版本替换。个人笔记单独保存；旧版与新版有差异，并不表示这些差异都是个人修改。不要在多个技能目录重复安装。Windows 的主目录通常为 `C:\Users\你的用户名`。

## 手动安装

下载 [仓库 ZIP](https://github.com/chenhao233/pmnote-skill/archive/refs/heads/main.zip)，解压后复制其中的 `pmnote/` 到对应目录。也可以下载 [Skill 安装包](https://github.com/chenhao233/pmnote-skill/releases/latest/download/pmnote.zip)，通过工具的「导入技能」入口安装。

## 确认生效

安装后新开一个对话，发出：

> 用 PMNote 带我学习：面对临近上线的新需求，项目经理有哪些判断方法？请先查阅相关原文，并附上出处。

正常回答应引用具体文章，而不只是列出目录。工具没有出现新技能时，刷新技能列表或重启后再试。

没有技能安装功能的 Agent，也可以直接读取[内容索引](https://github.com/chenhao233/pmnote-skill/blob/main/pmnote/references/index.md)。
