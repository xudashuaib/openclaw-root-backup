---
name: skill-audit
description: Audit other Skills for security vulnerabilities and risky patterns. Use when asked to check, review, audit, or scan a skill for safety, security risks, dangerous commands, embedded credentials, or suspicious code patterns. Triggers on "check skill safety", "audit skill", "scan skill for risks", "verify skill security", "review skill security", "skill 安全检查", "检查 skill 安全性".
---

# Skill Audit

Audit a skill for security concerns, dangerous patterns, and embedded secrets.

## Quick Start

```bash
python /root/.openclaw/skills/skill-audit/scripts/audit_skill.py <skill-path> [--json]
```

## What It Checks

| Category | Patterns Detected |
|----------|-------------------|
| 🔴 CRITICAL | `rm -rf /`, `mkfs`, `fdisk`, fork bombs, credential piping |
| 🟠 HIGH | `chmod 777`, shell injection (`curl \| sh`), writing to `/etc/` |
| 🟡 MEDIUM | `eval`, `exec`, `shell=True`, hardcoded passwords/keys, symlinks |
| 🟢 LOW | Force flags, package installs, HTTP (non-HTTPS) URLs |
| 🔵 INFO | Missing frontmatter, readable `/tmp` writes |

Also scans `references/` for embedded credentials (passwords, API keys, tokens).

## Output

The audit produces:
- **Risk Score** (0-100) with risk level label
- **Findings table** categorized by severity
- **Recommendations** on whether the skill is safe to use

## Usage Examples

### Audit a local skill:
```bash
python /root/.openclaw/skills/skill-audit/scripts/audit_skill.py /root/.openclaw/skills/feishu-doc
```

### Get JSON output for automation:
```bash
python /root/.openclaw/skills/skill-audit/scripts/audit_skill.py <skill-path> --json
```

### List all skills and audit one:
```bash
ls /root/.openclaw/skills/
python /root/.openclaw/skills/skill-audit/scripts/audit_skill.py /root/.openclaw/skills/<skill-name>
```

## Severity Reference

| Level | Score Weight | Action Required |
|-------|---------------|-----------------|
| 🔴 CRITICAL | 40 pts each | **Do not use** until fixed |
| 🟠 HIGH | 20 pts each | Review and remediate |
| 🟡 MEDIUM | 10 pts each | Consider fixing |
| 🟢 LOW | 5 pts each | Minor hardening |
| 🔵 INFO | 1 pt each | Informational |

Risk Score ≥70 = 🔴 VERY HIGH RISK
Risk Score 40-69 = 🟠 HIGH RISK
Risk Score 20-39 = 🟡 MODERATE RISK
Risk Score 5-19 = 🟢 LOW RISK
Risk Score <5 = ✅ MINIMAL RISK

## Limitations

- Static analysis only; cannot catch all runtime behavior issues
- Does not verify external API calls or network behavior at runtime
- Reference file scans limited to credential patterns; may miss other sensitive data
