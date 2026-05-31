# GitHub 使用指南

> 基于你实操过的 AgentFlow 项目，系统解释每一个 Git 操作。

---

## 一、Git 和 GitHub 是什么关系

| | Git | GitHub |
|------|-----|--------|
| 是什么 | 版本管理工具（软件） | 代码托管网站 |
| 装在哪 | 你电脑上 | 互联网上 |
| 谁开发的 | Linus Torvalds（Linux 之父） | 微软 |
| 类比 | 相册 App | 朋友圈 |

Git 管你电脑上的代码历史。GitHub 把这个历史同步到网上，让别人也能看到。

---

## 二、三个工作区域

```
工作目录                暂存区                 本地仓库             远程仓库（GitHub）
(你的文件)     →     (git add)      →    (git commit)     →    (git push)
                   "选照片"              "拍照存档"             "发朋友圈"

(你的文件)     ←     (git restore)  ←    (git reset)      ←    (git pull)
                    "撤销选择"            "恢复旧照片"           "下载更新"
```

每次修改代码的完整流程：

```
① 改代码
② git add .        → 把改动放入"待拍照"区域
③ git commit -m "" → 拍一张快照，附上说明
④ git push         → 把快照发到 GitHub
```

---

## 三、第一次推送项目（你刚做过的）

```bash
# 1. 进入项目文件夹
cd Desktop/myagent

# 2. 初始化 Git（让 Git 开始"盯"这个文件夹）
git init
# 只在第一次需要，之后不用

# 3. 把全部文件加入待提交清单
git add .

# 4. 提交（拍照存档）
git commit -m "第一次提交：完成 AgentFlow 项目"
# -m 后面是描述，随便写但要能看懂

# 5. 告诉 Git 你的 GitHub 地址
git remote add origin https://github.com/wzy106/agentflow.git
# 只在第一次需要，之后不用

# 6. 推送到 GitHub
git push -u origin master
# -u 表示"记住这个地址"，以后只写 git push 就行
```

**`git add .` 的点号是什么意思？**
`.` = 当前文件夹。`git add .` = 把当前文件夹里所有改动加入清单。你也可以只加一个文件：`git add server.py`。

---

## 四、日常修改代码后（最常用的三步）

```bash
git add .
git commit -m "修复了搜索工具的连接问题"
git push
```

**每次 commit 描述要写清楚改了什么**，三个月后回来看才知道这次干了啥。

好的描述：
```
"修复搜索工具 DuckDuckGo 连接超时"
"新增 /rag/upload 接口"
"优化 agent.py 的工具执行逻辑"
```

差的描述：
```
"改了一下"
"update"
"bug fix"
```

---

## 五、看看历史记录

```bash
# 看提交历史
git log

# 看精简版历史
git log --oneline

# 看当前状态（哪些文件改了、哪些还没提交）
git status
```

`git status` 输出解读：

```
Changes not staged for commit:      ← 改了但还没 git add
  modified:   server.py

Changes to be committed:            ← git add 过了，等 git commit
  new file:   README.md

nothing to commit, working tree clean   ← 一切正常，没有改动
```

---

## 六、如果改错了怎么办

### 6.1 改坏了还没 git add

```bash
# 恢复某个文件到最后一次 commit 的状态
git restore server.py

# 恢复所有文件
git restore .
```

### 6.2 git add 了但还没 commit

```bash
# 取消 add
git reset HEAD server.py
```

### 6.3 已经 commit 了但还没 push

```bash
# 修改最后一次 commit 的描述
git commit --amend -m "新的描述"
```

---

## 七、分支（Branch）基础

分支 = 代码的平行宇宙。一个项目可以有多条分支，各干各的。

```
master 分支：    主分支，稳定版本（你现在的）
feature 分支：   新功能开发分支（以后团队合作会用）
bugfix 分支：    修 bug 分支
```

### 创建并切换分支

```bash
git branch dev              # 创建一个叫 dev 的分支
git checkout dev            # 切换到 dev 分支
# 或者二合一：
git checkout -b dev         # 创建 + 切换
```

### 合并分支

```bash
git checkout master         # 回到主分支
git merge dev               # 把 dev 的改动合并到 master
```

**个人项目不需要分支**，直接在 master 上改。团队协作才用分支。

---

## 八、认证问题

### 推送时可能要你登录

```bash
Username: wzy106            # 你的 GitHub 用户名
Password: ghp_xxxxxxxx      # 不是登录密码！是 Personal Access Token
```

### Token 去哪拿

1. 打开 https://github.com/settings/tokens
2. Generate new token (classic)
3. 勾选 **repo**（全部勾上）
4. 生成后复制那串 `ghp_` 开头的代码
5. 粘贴到终端 Password 栏（**不会显示任何字符，正常**，直接回车）

Token 输过一次就记住了，以后不用再输。

---

## 九、从 GitHub 下载到新电脑

```bash
# 在新电脑上
git clone https://github.com/wzy106/agentflow.git

# 以后拉取最新更新
git pull
```

---

## 十、`.gitignore` 文件

有些文件不应该上传到 GitHub：

| 文件 | 为什么不上传 |
|------|-----------|
| `.env` | 里面有你的 API Key（密码） |
| `__pycache__/` | Python 自动生成的缓存，没用 |
| `data/` | 本地数据文件夹 |

创建 `.gitignore` 文件：

```
# 在项目根目录新建 .gitignore，写入：
.env
__pycache__/
*.pyc
data/
```

**⚠️ 如果 `.env` 已经推上去了**（你现在的仓库里有 `.env`），即使加了 `.gitignore` 也删不掉旧的。需要去 DeepSeek 重新生成一个 Key，把线上的旧 Key 废掉。

---

## 十一、命令速查表

| 命令 | 干什么 |
|------|--------|
| `git init` | 初始化（每个项目第一次用） |
| `git status` | 看看改了什么 |
| `git add .` | 把所有改动加入清单 |
| `git add 文件名` | 只加一个文件 |
| `git commit -m "描述"` | 拍照存档 |
| `git push` | 推到 GitHub |
| `git pull` | 从 GitHub 拉到本地 |
| `git log --oneline` | 看提交历史 |
| `git restore .` | 撤销所有改动 |
| `git clone 地址` | 下载一个仓库到本地 |
| `git remote -v` | 查看关联的 GitHub 地址 |

---

## 十二、你的 AgentFlow 仓库

- 仓库地址：`https://github.com/wzy106/agentflow`
- 本地路径：`C:\Users\wzyls\Desktop\myagent`
- 关联远程：`origin → https://github.com/wzy106/agentflow.git`
- 当前分支：`master`

以后改代码就是：
```bash
cd Desktop/myagent
git add .
git commit -m "描述"
git push
```

三步，永远不会变。
