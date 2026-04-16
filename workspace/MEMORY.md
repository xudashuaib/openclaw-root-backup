# MEMORY.md - Long-Term Memory

## 关于用户

- 通过飞书与我对话（ou_451d71ab5382024db03f3a5c37dcde02）
- 技术能力强：Linux运维、AI工具安装（OpenClaw、Hermes Agent）
- 正在使用/研究多个AI Agent平台
- 有A股投资分析需求，重点关注兆易创新(603986.SH)

## 重要事件记录

### 2026-04-15 今天的工作

**兆易创新(603986)分析**
- 早盘预测：09:43发布，方向"高开低走/多头陷阱"，基准273-277
- 午盘复盘：272支撑完美验证，收盘274，预测评分9/10（早盘）、9.5/10（午盘）
- 全天走势：开盘285→高台跳水→271.98→收274，全天-2.15%
- 注意：12:00定时任务失败（文件编辑冲突），手动补录

**Hermes Agent 安装**
- 从 Nous Research 安装了 hermes-agent（GitHub镜像下载）
- 成功接入 MiniMax Coding Plan (sk-cp-xxx)：base_url = https://api.minimax.chat/v1
- 注意：minimax-cn provider 的域名 api.minmax.chat 不通，需用 custom provider
- 微信接入成功（iLink Bot方式，WEIXIN_ACCOUNT_ID=406cbccba0ae@im.bot）

**OpenClaw .hermes 误删**
- 用户误将 /root/.hermes（HTTPS://github.com/NousResearch/hermes-agent）当作要删除的目录
- 实际删的是 Hermes Agent 的运行时目录，不影响 OpenClaw
- OpenClaw 的工作目录在 ~/.openclaw/，完全未动

**OpenClaw网关**：运行在 192.168.116.130:18789
**Hermes网关**：运行在 systemd 服务，微信已连接

## 关键配置

- MiniMax API: base_url = https://api.minimax.chat/v1, provider = custom
- 兆易创新数据目录: ~/.openclaw/workspace/stocks/603986_gigadevice/
- Hermes 目录: /tmp/hermes-agent-main/ (临时，重启后需重装)

### 2026-04-16 凌晨 备份体系建立
- GitHub仓库: `openclaw-root-backup` → 备份整个 `~/.openclaw/`（含credentials，仅排除logs/.discovery）
- 备份工具: rsync + git
- 定时备份: 每天16:05(Mon-Fri)自动 rsync + commit + push
- 本地备份目录: `~/.openclaw-backup/`
- 注意: github.com:443当前网络不通，等待恢复后自动推送
- GitHub仓库: https://github.com/xudashuaib/openclaw-workspace
- 首次推送: 246文件，commit: 983581b
- 定时备份: 每天16:05(Mon-Fri)自动 git add → commit → push

**恢复方式（区别场景）：**
- 工作区完好: `git pull origin main`
- 工作区损坏: `mv ~/.openclaw/workspace ~/.openclaw/workspace.broken` → `git clone https://github.com/xudashuaib/openclaw-workspace.git ~/.openclaw/workspace` → `git submodule update --init --recursive`
