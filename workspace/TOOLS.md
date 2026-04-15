# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## Active Projects

When working on a specific task, check here first for project context.

| Project | Root | Key Files |
|---------|------|----------|
| 兆易创新(603986)分析 | `/root/.openclaw/workspace/stocks/603986_gigadevice/` | `PROJECT_PLAN.md`（完整方案）<br>`tracking/daily_prediction.json`（每日预测）<br>`tracking/daily_price.json`（每日行情）<br>`model/model_history.json`（模型版本）<br>`reports/2026/`（分析报告） |

---

## How to Navigate a Stock Analysis Task

When resuming work on 兆易创新(603986):

1. **Read `PROJECT_PLAN.md`** — full task plan, dimensions, workflow, file structure
2. **Read `model/model_history.json`** — current model version, what changed
3. **Read `tracking/daily_prediction.json`** — today's prediction status + accuracy stats
4. **Read `tracking/daily_price.json`** — latest price data
5. **Read `reports/2026/`** — latest analysis reports by date

When updating daily prediction:
- Write to `tracking/daily_prediction.json`
- Write to `tracking/daily_price.json`
- When model changes: append to `model/model_history.json`

## File Writing Rules

Always use ISO date format (YYYY-MM-DD) in filenames.
All daily tracking files go under `tracking/`.
All raw data goes under `raw/YYYY-MM/`.
All reports go under `reports/YYYY/`.

---

Add whatever helps you do your job. This is your cheat sheet.
