#!/usr/bin/env python3
"""
Skill Security Audit Script
Scans a skill's SKILL.md and bundled resources for security concerns.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Severity levels
CRITICAL = "🔴 CRITICAL"
HIGH = "🟠 HIGH"
MEDIUM = "🟡 MEDIUM"
LOW = "🟢 LOW"
INFO = "🔵 INFO"

# Patterns that indicate potential security issues
DANGEROUS_PATTERNS = {
    CRITICAL: [
        (r'rm\s+-rf\s+/', "Recursive force delete of root directory"),
        (r'mkfs', "Filesystem format command"),
        (r'fdisk', "Disk partitioning command"),
        (r'dd\s+if=.*of=/dev/', "Direct disk write operation"),
        (r'shred\s+-', "Secure file deletion"),
        (r':(){\s*:\|:&\s*};:', "Fork bomb detected"),
        (r'curl.*\b(secret|password|token|key).*\|', "Potential credential exfiltration via pipe"),
        (r'wget.*\b(secret|password|token|key).*\|', "Potential credential exfiltration via pipe"),
        (r'system\s*\(\s*["\'].*rm\s', "Shell injection risk with rm"),
        (r'exec\s*\(\s*\$', "Dynamic code execution from variable"),
        (r'eval\s*\(\s*\$', "Dynamic code execution from variable"),
    ],
    HIGH: [
        (r'chmod\s+777', "World-writable permission (777)"),
        (r'chmod\s+000', "Removing all permissions"),
        (r'curl\s+--data["\']?\s*[@\$]', "curl with variable data - potential injection"),
        (r'wget\s+--[a-z]+=["\'].*\$', "wget with variable - potential injection"),
        (r'sudo\s+su', "Escalating to root without restrictions"),
        (r'>\s*/etc/', "Writing to system configuration file"),
        (r'>\s*/var/', "Writing to system directory"),
        (r'cp\s+.*\$', "Copying with variable - verify source is trusted"),
        (r'mv\s+.*\$', "Moving with variable - verify source is trusted"),
        (r'cat\s+.*\.env', "Reading environment/secret files"),
        (r'source\s+.*\.env', "Sourcing environment/secret files"),
    ],
    MEDIUM: [
        (r'curl\s+http[s]?://', "HTTP request - data not encrypted in transit"),
        (r'wget\s+http[s]?://', "HTTP request - data not encrypted in transit"),
        (r'eval\s+', "Use of eval - can lead to injection if input is untrusted"),
        (r'exec\s+', "Use of exec - can lead to injection if input is untrusted"),
        (r'os\.system\s*\(', "os.system call - shell injection risk"),
        (r'subprocess.*shell\s*=\s*True', "Shell=True in subprocess - injection risk"),
        (r'password\s*=\s*["\'][^"\']{0,20}["\']', "Hardcoded password or short secret"),
        (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
        (r'token\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded token"),
        (r'secret\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret"),
    ],
    LOW: [
        (r'--force', "Force flag - may override safety checks"),
        (r'-f\s+', "Force flag - may override safety checks"),
        (r'yum\s+install', "Installing packages via yum"),
        (r'apt-get\s+install', "Installing packages via apt-get"),
        (r'pip\s+install', "Installing Python packages"),
        (r'npm\s+install', "Installing Node packages"),
        (r'>\s*/tmp/', "Writing to /tmp - data may be world-readable"),
    ],
}

SUSPICIOUS_TOOL_PATTERNS = {
    "exec": ["dangerous", "escalat", "inject", "exfil", "exfiltrat"],
    "write": ["credential", "secret", "password", "token", "key", "/etc/", "/root/"],
    "read": ["credential", "secret", "password", "token", "key", "/etc/", "/root/"],
    "web_fetch": ["internal", "localhost", "127.0.0.1", "metadata"],
    "web_search": ["password", "secret", "token", "api key"],
}


def scan_file_content(content: str, filename: str = "unknown") -> List[Dict]:
    """Scan file content for dangerous patterns."""
    findings = []
    
    for severity, patterns in DANGEROUS_PATTERNS.items():
        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                context = content[max(0, match.start() - 40):match.end() + 40]
                findings.append({
                    "severity": severity,
                    "file": filename,
                    "line": line_num,
                    "pattern": description,
                    "match": match.group(),
                    "context": context.replace('\n', ' ')
                })
    
    return findings


def scan_skill_md(skill_path: Path) -> Tuple[List[Dict], Dict]:
    """Scan SKILL.md for security issues."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return [], {}
    
    content = skill_md.read_text(encoding='utf-8')
    findings = scan_file_content(content, "SKILL.md")
    
    # Check frontmatter
    frontmatter = {}
    if content.startswith('---'):
        end = content.find('---', 3)
        if end > 0:
            fm_text = content[3:end].strip()
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    frontmatter[key.strip()] = val.strip()
    
    # Check for missing description
    if 'description' not in frontmatter:
        findings.append({
            "severity": INFO,
            "file": "SKILL.md",
            "line": 1,
            "pattern": "Missing description in frontmatter",
            "match": "",
            "context": "SKILL.md should have a description field in YAML frontmatter"
        })
    
    # Check for tool access patterns in description
    if 'description' in frontmatter:
        desc_lower = frontmatter['description'].lower()
        for tool, suspicious_words in SUSPICIOUS_TOOL_PATTERNS.items():
            for word in suspicious_words:
                if word.lower() in desc_lower:
                    findings.append({
                        "severity": LOW,
                        "file": "SKILL.md (frontmatter)",
                        "line": 1,
                        "pattern": f"Tool '{tool}' mentioned with '{word}' in description",
                        "match": word,
                        "context": frontmatter['description'][:200]
                    })
    
    return findings, frontmatter


def scan_scripts(skill_path: Path) -> List[Dict]:
    """Scan all scripts in the skill directory."""
    findings = []
    
    for script_path in skill_path.rglob("scripts/*"):
        if script_path.is_file() and not script_path.name.startswith('.'):
            try:
                content = script_path.read_text(encoding='utf-8', errors='ignore')
                file_findings = scan_file_content(content, str(script_path.relative_to(skill_path)))
                findings.extend(file_findings)
            except Exception as e:
                findings.append({
                    "severity": INFO,
                    "file": str(script_path),
                    "line": 0,
                    "pattern": f"Could not read file: {e}",
                    "match": "",
                    "context": ""
                })
    
    return findings


def scan_references(skill_path: Path) -> List[Dict]:
    """Scan reference files for embedded secrets."""
    findings = []
    
    for ref_path in skill_path.rglob("references/*"):
        if ref_path.is_file():
            try:
                content = ref_path.read_text(encoding='utf-8', errors='ignore')
                
                # Check for embedded credentials
                credential_patterns = [
                    (r'password\s*[:=]\s*["\'][^"\']{3,}["\']', "Embedded password"),
                    (r'api[_-]?key\s*[:=]\s*["\'][^"\']{10,}["\']', "Embedded API key"),
                    (r'token\s*[:=]\s*["\'][^"\']{10,}["\']', "Embedded token"),
                    (r'Bearer\s+[a-zA-Z0-9\-_\.]+', "Embedded Bearer token"),
                    (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
                    (r'AKIA[A-Z0-9]{16}', "AWS Access Key ID"),
                ]
                
                for pattern, description in credential_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append({
                            "severity": HIGH,
                            "file": str(ref_path.relative_to(skill_path)),
                            "line": line_num,
                            "pattern": description,
                            "match": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                            "context": f"Found {description} in reference file - ensure this is intentional and not a leak"
                        })
            except Exception as e:
                findings.append({
                    "severity": INFO,
                    "file": str(ref_path),
                    "line": 0,
                    "pattern": f"Could not read file: {e}",
                    "match": "",
                    "context": ""
                })
    
    return findings


def scan_symlinks(skill_path: Path) -> List[Dict]:
    """Check for symlinks which may be a security concern."""
    findings = []
    
    for path in skill_path.rglob("*"):
        if path.is_symlink():
            target = path.readlink()
            findings.append({
                "severity": MEDIUM,
                "file": str(path.relative_to(skill_path)),
                "line": 0,
                "pattern": "Symbolic link detected",
                "match": f"-> {target}",
                "context": "Symlinks can be changed to point to different files - verify target is expected"
            })
    
    return findings


def generate_report(skill_path: Path) -> Dict:
    """Generate a full security audit report for a skill."""
    skill_name = skill_path.name
    
    all_findings = []
    
    # Scan SKILL.md
    md_findings, frontmatter = scan_skill_md(skill_path)
    all_findings.extend(md_findings)
    
    # Scan scripts
    all_findings.extend(scan_scripts(skill_path))
    
    # Scan references
    all_findings.extend(scan_references(skill_path))
    
    # Check for symlinks
    all_findings.extend(scan_symlinks(skill_path))
    
    # Categorize by severity
    by_severity = {CRITICAL: [], HIGH: [], MEDIUM: [], LOW: [], INFO: []}
    for f in all_findings:
        by_severity[f["severity"]].append(f)
    
    # Calculate risk score
    risk_score = 0
    risk_score += len(by_severity[CRITICAL]) * 40
    risk_score += len(by_severity[HIGH]) * 20
    risk_score += len(by_severity[MEDIUM]) * 10
    risk_score += len(by_severity[LOW]) * 5
    risk_score += len(by_severity[INFO]) * 1
    
    max_possible = 100
    risk_percent = min(100, risk_score)
    
    if risk_percent >= 70:
        risk_level = "🔴 VERY HIGH RISK"
    elif risk_percent >= 40:
        risk_level = "🟠 HIGH RISK"
    elif risk_percent >= 20:
        risk_level = "🟡 MODERATE RISK"
    elif risk_percent >= 5:
        risk_level = "🟢 LOW RISK"
    else:
        risk_level = "✅ MINIMAL RISK"
    
    return {
        "skill_name": skill_name,
        "skill_path": str(skill_path),
        "frontmatter": frontmatter,
        "risk_score": risk_percent,
        "risk_level": risk_level,
        "total_findings": len(all_findings),
        "by_severity": by_severity,
        "all_findings": all_findings,
        "summary": {
            "critical": len(by_severity[CRITICAL]),
            "high": len(by_severity[HIGH]),
            "medium": len(by_severity[MEDIUM]),
            "low": len(by_severity[LOW]),
            "info": len(by_severity[INFO]),
        }
    }


def format_report(report: Dict) -> str:
    """Format the audit report as a readable markdown string."""
    lines = [
        f"# 🔍 Skill Security Audit Report",
        f"",
        f"## Skill: `{report['skill_name']}`",
        f"**Path:** `{report['skill_path']}`",
        f"",
        f"## Risk Assessment",
        f"",
        f"**Risk Score:** {report['risk_score']}/100 — {report['risk_level']}",
        f"",
        f"## Summary",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| 🔴 CRITICAL | {report['summary']['critical']} |",
        f"| 🟠 HIGH | {report['summary']['high']} |",
        f"| 🟡 MEDIUM | {report['summary']['medium']} |",
        f"| 🟢 LOW | {report['summary']['low']} |",
        f"| 🔵 INFO | {report['summary']['info']} |",
        f"",
    ]
    
    if report['frontmatter']:
        lines.extend([
            "## Frontmatter",
            "",
            "```yaml"
        ])
        for k, v in report['frontmatter'].items():
            lines.append(f"{k}: {v}")
        lines.append("```")
        lines.append("")
    
    if report['all_findings']:
        lines.extend([
            "## Findings",
            ""
        ])
        
        for severity in [CRITICAL, HIGH, MEDIUM, LOW, INFO]:
            findings = report['by_severity'][severity]
            if findings:
                lines.append(f"### {severity}")
                lines.append("")
                for f in findings:
                    lines.append(f"**{f['file']}** (line {f['line']})")
                    lines.append(f"- Pattern: {f['pattern']}")
                    if f['match']:
                        lines.append(f"- Match: `{(f['match'][:100])}`")
                    lines.append(f"- Context: `{(f['context'][:150])}`")
                    lines.append("")
    else:
        lines.extend([
            "## Findings",
            "",
            "✅ No security issues detected.",
            ""
        ])
    
    # Recommendations
    lines.extend([
        "## Recommendations",
        ""
    ])
    
    critical_count = report['summary']['critical']
    high_count = report['summary']['high']
    
    if critical_count > 0:
        lines.append(f"⚠️ **CRITICAL issues found ({critical_count}). Do not use this skill until issues are resolved.**")
    elif high_count > 0:
        lines.append(f"🔴 **High-risk issues found ({high_count}). Review carefully before deployment.**")
    elif report['summary']['medium'] > 0:
        lines.append(f"🟡 Moderate issues found. Consider addressing before production use.")
    else:
        lines.append(f"✅ Skill appears safe for use with standard precautions.")
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python audit_skill.py <skill-path> [--json]")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1])
    
    if not skill_path.exists():
        print(f"Error: Path does not exist: {skill_path}")
        sys.exit(1)
    
    report = generate_report(skill_path)
    
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(format_report(report))


if __name__ == "__main__":
    main()
