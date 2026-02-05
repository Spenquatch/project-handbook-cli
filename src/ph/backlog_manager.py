from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from . import clock
from .sprint import get_sprint_dates


class BacklogManager:
    def __init__(self, *, project_root: Path, env: dict[str, str] | None = None) -> None:
        self.project_root = Path(project_root).absolute()
        self.env = env
        self.backlog_dir = self.project_root / "backlog"
        self.index_file = self.backlog_dir / "index.json"

        # Severity rubric (ported from v0).
        self.severity_rubric: dict[str, dict[str, Any]] = {
            "P0": {
                "name": "Critical",
                "color": "🔴",
                "criteria": [
                    "Production outage affecting >50% of users",
                    "Active security exploit",
                    "Data loss or corruption",
                    "Complete feature failure in production",
                ],
                "action": "Always interrupts current sprint",
            },
            "P1": {
                "name": "High",
                "color": "🟠",
                "criteria": [
                    "Service degradation affecting 10-50% of users",
                    "Major feature broken but workaround exists",
                    "Security vulnerability (not actively exploited)",
                    "Significant performance degradation",
                ],
                "action": "Addressed in next sprint",
            },
            "P2": {
                "name": "Medium",
                "color": "🟡",
                "criteria": [
                    "Issue affecting <10% of users",
                    "Minor feature malfunction",
                    "UI/UX issues with moderate impact",
                    "Non-critical performance issues",
                ],
                "action": "Queued in backlog",
            },
            "P3": {
                "name": "Low",
                "color": "🟢",
                "criteria": [
                    "Cosmetic issues",
                    "Developer experience improvements",
                    "Documentation gaps",
                    "Nice-to-have enhancements",
                ],
                "action": "Backlog queue, low priority",
            },
            "P4": {
                "name": "Wishlist",
                "color": "⚪",
                "criteria": ["Future enhancements", "Experimental features", "Long-term improvements"],
                "action": "Consider for parking lot",
            },
        }

    def add_issue(
        self,
        issue_type: str,
        title: str,
        severity: str,
        desc: str = "",
        owner: str = "",
        impact: str = "",
        workaround: str = "",
    ) -> str | None:
        """Add a new issue to the backlog (ported from v0)."""
        input_type = (issue_type or "").strip().lower()
        issue_type = self._normalize_issue_type(issue_type)
        if issue_type not in ["bugs", "wildcards", "work-items"]:
            print(f"Error: Invalid type '{issue_type}'")
            print("Valid types: bugs, wildcards, work-items")
            return None

        if severity not in self.severity_rubric:
            print(f"Error: Invalid severity '{severity}'")
            print("Valid severities: P0, P1, P2, P3, P4")
            return None

        # Create directory structure
        type_dir = self.backlog_dir / issue_type
        type_dir.mkdir(parents=True, exist_ok=True)

        # Generate issue ID
        issue_id = self._generate_issue_id(issue_type, severity)
        issue_dir = type_dir / issue_id

        if issue_dir.exists():
            print(f"Error: Issue '{issue_id}' already exists")
            return None

        issue_dir.mkdir(parents=True)

        # Create README.md with front matter
        readme_path = issue_dir / "README.md"
        created = clock.now(env=self.env).strftime("%Y-%m-%d")
        front_matter = {
            "title": title,
            "type": issue_type,
            "input_type": input_type or issue_type,
            "severity": severity,
            "status": "open",
            "created": created,
            "owner": owner or "unassigned",
            "impact": impact,
            "workaround": workaround,
        }

        severity_info = self.severity_rubric[severity]

        content = f"""---
title: {front_matter["title"]}
type: {front_matter["type"]}
input_type: {front_matter["input_type"]}
severity: {front_matter["severity"]}
status: {front_matter["status"]}
created: {front_matter["created"]}
owner: {front_matter["owner"]}
---

# {severity_info["color"]} [{severity}] {title}

**Severity:** {severity} - {severity_info["name"]}  
**Action Required:** {severity_info["action"]}

## Description

{desc}

## Impact

{impact or "_Describe the impact on users, systems, or business_"}

## Workaround

{workaround or "_Document any temporary workaround if available_"}

## Root Cause Analysis

_To be completed during investigation_

## Solution Options

### Option 1: Quick Fix
_Describe quick/hotfix approach_

### Option 2: Proper Fix
_Describe comprehensive solution_

## Investigation Notes

_Add investigation findings here_
"""

        readme_path.write_text(content, encoding="utf-8")

        # For P0 issues, create triage analysis template
        if severity == "P0":
            triage_path = issue_dir / "triage.md"
            triage_content = self._generate_triage_template(title, desc, impact)
            triage_path.write_text(triage_content, encoding="utf-8")
            print("  🎯 Created P0 triage template: triage.md")

        print(f"✅ Created backlog issue: {issue_id}")
        print(f"   Severity: {severity_info['color']} {severity} - {severity_info['name']}")
        print(f"   Location: {issue_dir.relative_to(self.project_root)}")

        # Update index
        self.update_index()

        # Alert for P0
        if severity == "P0":
            print("\n" + "=" * 60)
            print("🚨 P0 CRITICAL ISSUE - IMMEDIATE ACTION REQUIRED 🚨")
            print("=" * 60)
            print(f"Issue: {title}")
            print(f"Impact: {impact or 'Not specified'}")
            print("\nRecommended actions:")
            print(f"1. Run: ph backlog triage --issue {issue_id} to generate AI analysis")
            print("2. Notify incident response team")
            print("3. Consider interrupting current sprint")
            print("=" * 60)

        return issue_id

    def list_issues(self, severity: str | None = None, category: str | None = None, format: str = "table") -> None:
        """List backlog issues (ported from v0, with category filtering per v1 contract)."""
        self.update_index(print_summary=format != "json")

        index_data = json.loads(self.index_file.read_text(encoding="utf-8"))

        if format == "json":
            print(json.dumps(index_data, indent=2))
            return

        print("\n📝 ISSUE BACKLOG")
        print("=" * 80)

        if index_data["total_items"] == 0:
            print("No issues in backlog")
            return

        # Count by severity
        p0_count = len(index_data["by_severity"]["P0"])
        p1_count = len(index_data["by_severity"]["P1"])

        if p0_count > 0:
            print(f"🚨 WARNING: {p0_count} P0 CRITICAL ISSUES REQUIRE IMMEDIATE ACTION")
        if p1_count > 0:
            print(f"⚠️  Note: {p1_count} P1 high priority issues for next sprint")

        print()

        for sev in ["P0", "P1", "P2", "P3", "P4"]:
            if severity and severity != sev:
                continue

            items = [item for item in index_data["items"] if item.get("severity") == sev]
            if category:
                items = [item for item in items if item.get("type") == category]

            if not items:
                continue

            sev_info = self.severity_rubric[sev]
            print(f"{sev_info['color']} {sev} - {sev_info['name']} ({len(items)} issues)")
            print("-" * 40)

            for item in items:
                issue_type = item.get("type", "unknown")
                created = item.get("created", "unknown")
                status = item.get("status", "open")
                owner = item.get("owner", "unassigned")
                title = item.get("title", item["id"])
                triage = "🎯" if item.get("has_triage") else ""

                print(f"  • {item['id']} {triage}")
                print(f"    {title}")
                print(f"    Type: {issue_type} | Status: {status} | Owner: {owner}")
                print(f"    Created: {created}")
                print()

        print(f"\nTotal issues: {index_data['total_items']}")

        print("\nBy Severity:")
        for sev in ["P0", "P1", "P2", "P3", "P4"]:
            count = len(index_data["by_severity"][sev])
            if count > 0:
                sev_info = self.severity_rubric[sev]
                print(f"  {sev_info['color']} {sev}: {count} issues")

        print(f"\nLast updated: {index_data.get('last_updated', 'never')}")

    def triage_issue(self, issue_id: str) -> bool:
        """Generate or display triage analysis for an issue (ported from v0)."""
        self.update_index(print_summary=False)

        index_data = json.loads(self.index_file.read_text(encoding="utf-8"))
        issue: dict[str, Any] | None = None

        for item in index_data["items"]:
            if item["id"] == issue_id:
                issue = item
                break

        if not issue:
            print(f"Error: Issue '{issue_id}' not found")
            return False

        issue_path = self.project_root / issue["path"]
        triage_path = issue_path / "triage.md"

        if triage_path.exists():
            print(f"\n🎯 TRIAGE ANALYSIS: {issue_id}")
            print("=" * 80)
            print(triage_path.read_text(encoding="utf-8"), end="")
            return True

        print(f"No triage analysis found for {issue_id}")
        if issue.get("severity") == "P0":
            print("Generating triage template...")

            # v0 reads the README but only uses the index-derived fields in the template inputs.
            readme_path = issue_path / "README.md"
            if readme_path.exists():
                _ = readme_path.read_text(encoding="utf-8", errors="ignore")

            title = issue.get("title", "Unknown Issue")
            desc = "See README.md for details"
            impact = issue.get("impact", "Not specified")

            triage_content = self._generate_triage_template(title, desc, impact)
            triage_path.write_text(triage_content, encoding="utf-8")
            print(f"✅ Generated triage template: {triage_path.relative_to(self.project_root)}")
            print("\nEdit the template to complete the analysis.")

        return True

    def assign_to_sprint(self, issue_id: str, sprint: str = "current", *, scope: str) -> bool:
        """Assign a backlog issue to a sprint (ported from v0)."""
        self.update_index()

        index_data = json.loads(self.index_file.read_text(encoding="utf-8"))
        issue: dict[str, Any] | None = None

        for item in index_data["items"]:
            if item["id"] == issue_id:
                issue = item
                break

        if not issue:
            print(f"Error: Issue '{issue_id}' not found")
            return False

        resolved_sprint = self._resolve_sprint_arg(sprint)
        if not resolved_sprint:
            print(f"Error: Could not resolve sprint '{sprint}'.")
            print(
                "Tip: set sprints/current (via sprint planning), or pass an explicit sprint id like SPRINT-YYYY-MM-DD."
            )
            return False

        print(f"\nAssigning {issue_id} to sprint {resolved_sprint}")
        print(f"Severity: {issue.get('severity', 'unknown')}")
        print(f"Title: {issue.get('title', 'unknown')}")

        issue_path = self.project_root / issue["path"]
        if not self._update_issue_front_matter(issue_path, {"sprint": resolved_sprint}):
            return False

        self.update_index()

        print(f"\n✅ Recorded assignment: {issue_id} → {resolved_sprint}")
        print("Next steps:")
        task_create_cmd = "ph --scope system task create" if scope == "system" else "ph task create"
        print(
            "1. Create/assign the actual sprint task via "
            f"'{task_create_cmd} ...' (feature + decision required; discovery tasks may use "
            "session=research-discovery decision=DR-XXXX)."
        )
        print("2. If needed, update the sprint plan lanes/integration tasks to reflect the new work.")

        return True

    def _get_active_sprint_id(self) -> str | None:
        link = self.project_root / "sprints" / "current"
        if not link.exists():
            return None
        try:
            resolved = link.resolve()
            if resolved.exists():
                return resolved.name
        except Exception:
            return None
        return None

    def _resolve_sprint_arg(self, sprint: str) -> str | None:
        if not sprint:
            return None
        sprint = sprint.strip()
        if sprint == "current":
            return self._get_active_sprint_id()
        if sprint == "next":
            current = self._get_active_sprint_id()
            if not current:
                return None
            return self._compute_next_sprint_id(current)
        return sprint

    def _compute_next_sprint_id(self, current_sprint_id: str) -> str | None:
        try:
            start, _end = get_sprint_dates(current_sprint_id)
        except Exception:
            return None

        next_start = start + timedelta(days=7)
        parts = current_sprint_id.split("-")
        if len(parts) >= 3 and parts[2].startswith("W"):
            iso = next_start.isocalendar()
            return f"SPRINT-{iso.year}-W{iso.week:02d}"

        return f"SPRINT-{next_start:%Y-%m-%d}"

    def _update_issue_front_matter(self, issue_dir: Path, updates: dict[str, str]) -> bool:
        readme_path = issue_dir / "README.md"
        if not readme_path.exists():
            print(f"Error: Missing README.md for issue at {issue_dir}")
            return False

        content = readme_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            print(f"Error: README.md missing front matter: {readme_path}")
            return False

        end_marker = content.find("---", 3)
        if end_marker == -1:
            print(f"Error: README.md front matter malformed: {readme_path}")
            return False

        front_matter = content[3:end_marker].strip("\n")
        body = content[end_marker + 3 :]

        rows = front_matter.splitlines()
        existing: dict[str, str] = {}
        order: list[str] = []
        for row in rows:
            if ":" not in row:
                continue
            key, value = row.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            existing[key] = value
            order.append(key)

        for key, value in updates.items():
            if value is None:
                continue
            existing[key] = str(value)
            if key not in order:
                order.append(key)

        rebuilt = "\n".join([f"{key}: {existing[key]}" for key in order if key in existing])
        readme_path.write_text(f"---\n{rebuilt}\n---{body}", encoding="utf-8")
        return True

    def show_stats(self, *, ph_root: Path) -> None:
        """Display backlog statistics and analysis (ported from v0)."""
        from datetime import datetime

        validation_rules_path = ph_root / "process" / "checks" / "validation_rules.json"
        validation_rules: dict[str, Any] = {}
        if validation_rules_path.exists():
            validation_rules = json.loads(validation_rules_path.read_text(encoding="utf-8"))

        backlog_config = validation_rules.get("backlog", {})
        _capacity_config = backlog_config.get("capacity_allocation", {})
        _escalation_thresholds = backlog_config.get("escalation_thresholds", {})

        if not self.index_file.exists():
            self.update_index()

        index_data = json.loads(self.index_file.read_text(encoding="utf-8"))

        print("\n📊 BACKLOG STATISTICS")
        print("=" * 80)

        print("\n📈 Summary")
        print("-" * 40)
        print(f"Total Issues: {index_data['total_items']}")
        print(f"Categories: {', '.join(index_data['by_category'].keys())}")
        print(f"Last Updated: {index_data['last_updated']}")

        print("\n🎯 Severity Distribution")
        print("-" * 40)
        severity_stats: dict[str, int] = {}
        for item in index_data["items"]:
            severity = item.get("severity", "P2")
            severity_stats[severity] = severity_stats.get(severity, 0) + 1

        for severity in ["P0", "P1", "P2", "P3", "P4"]:
            count = severity_stats.get(severity, 0)
            percentage = (count / max(index_data["total_items"], 1)) * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)

            severity_info = self.severity_rubric.get(severity, {})
            color = severity_info.get("color", "")
            print(f"{color:4} {severity}: {count:3} ({percentage:5.1f}%) |{bar}|")

        print("\n📁 Category Breakdown")
        print("-" * 40)
        for category, items in index_data["by_category"].items():
            print(f"{category.capitalize():15} {len(items):3} issues")

        print("\n⏱️ Age Analysis")
        print("-" * 40)
        now = clock.now(env=self.env)
        age_buckets: dict[str, int] = {"<24h": 0, "1-3d": 0, "3-7d": 0, "1-2w": 0, "2-4w": 0, ">1m": 0}

        for item in index_data["items"]:
            created = item.get("created", "")
            if created:
                try:
                    created_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    age = now - created_date

                    if age < timedelta(days=1):
                        age_buckets["<24h"] += 1
                    elif age < timedelta(days=3):
                        age_buckets["1-3d"] += 1
                    elif age < timedelta(days=7):
                        age_buckets["3-7d"] += 1
                    elif age < timedelta(days=14):
                        age_buckets["1-2w"] += 1
                    elif age < timedelta(days=28):
                        age_buckets["2-4w"] += 1
                    else:
                        age_buckets[">1m"] += 1
                except Exception:
                    pass

        for bucket, count in age_buckets.items():
            if count > 0:
                print(f"{bucket:10} {count:3} issues")

        print("\n💼 Capacity Impact")
        print("-" * 40)
        p0_p1_count = severity_stats.get("P0", 0) + severity_stats.get("P1", 0)

        if p0_p1_count > 0:
            print(f"P0/P1 Issues: {p0_p1_count}")
            print("Reactive Capacity Required: ~20% of sprint")

            if severity_stats.get("P0", 0) > 0:
                print("⚠️  P0 ALERT: Immediate interrupt required!")
            if severity_stats.get("P1", 0) > 3:
                print("⚠️  P1 WARNING: High reactive load for next sprint")
        else:
            print("✅ No P0/P1 issues - full planned capacity available")

        print("\n💡 Recommendations")
        print("-" * 40)

        if severity_stats.get("P0", 0) > 0:
            print("🔴 Address P0 issues immediately - interrupt current sprint")
        if severity_stats.get("P1", 0) > 0:
            print("🟠 Plan P1 issues for next sprint (use 20% reactive capacity)")
        if severity_stats.get("P2", 0) > 5:
            print("🟡 Consider prioritizing P2 backlog in upcoming sprints")
        if severity_stats.get("P4", 0) > 10:
            print("⚪ Review P4 items for parking lot candidates")

        print("\n" + "=" * 80)

    def show_rubric(self) -> None:
        """Display the severity rubric (ported from v0)."""
        print("\n📏 ISSUE SEVERITY RUBRIC")
        print("=" * 80)

        for severity, info in self.severity_rubric.items():
            print(f"\n{info['color']} {severity} - {info['name']}")
            print("-" * 40)
            print(f"Action: {info['action']}")
            print("\nCriteria:")
            for criterion in info["criteria"]:
                print(f"  • {criterion}")

        print("\n" + "=" * 80)
        print("\n💡 Guidelines:")
        print("  • P0 issues ALWAYS interrupt the current sprint")
        print("  • P1 issues are addressed in the next sprint")
        print("  • P2-P3 issues queue in the backlog")
        print("  • P4 issues are candidates for the parking lot")
        print("  • Use 'ph backlog triage' for P0 decision support")

    def _normalize_issue_type(self, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized in {"bug", "bugs"}:
            return "bugs"
        if normalized in {"wildcard", "wildcards"}:
            return "wildcards"
        if normalized in {
            "work",
            "work-item",
            "work-items",
            "enhancement",
            "enhancements",
            "improvement",
            "improvements",
        }:
            return "work-items"
        return normalized

    def _generate_issue_id(self, issue_type: str, severity: str) -> str:
        """Generate a unique issue ID (ported from v0)."""
        if issue_type == "bugs":
            prefix = "BUG"
        elif issue_type == "wildcards":
            prefix = "WILD"
        else:
            prefix = "WORK"
        # Include seconds so multiple issues can be created within the same minute.
        timestamp = clock.now(env=self.env).strftime("%Y%m%d-%H%M%S")
        return f"{prefix}-{severity}-{timestamp}"

    def _generate_triage_template(self, title: str, desc: str, impact: str) -> str:
        """Generate AI triage analysis template for P0 issues (ported from v0)."""
        return f"""# P0 Triage Analysis: {title}

Generated: {clock.now(env=self.env).strftime("%Y-%m-%d %H:%M")}

## 🎯 Problem Statement

**Issue:** {title}

**Description:** {desc}

**Impact Metrics:**
- Users affected: _[To be determined]_
- Services impacted: _[To be determined]_
- Revenue impact: _[To be determined]_
- Data at risk: _[To be determined]_

## 🛠️ Solution Options Analysis

### Option 1: Hotfix Approach

**Description:** _[Quick tactical fix to stop the bleeding]_

**Pros:**
- ✅ Can be deployed immediately
- ✅ Minimal testing required
- ✅ Low risk of additional issues

**Cons:**
- ❌ Technical debt created
- ❌ May not address root cause
- ❌ Requires follow-up work

**Time Estimate:** _[X hours]_

**Interruption Cost:** 
- Sprint tasks delayed: _[List affected tasks]_
- Team members required: _[Number and roles]_

### Option 2: Proper Fix

**Description:** _[Comprehensive solution addressing root cause]_

**Pros:**
- ✅ Addresses root cause
- ✅ Prevents recurrence
- ✅ Improves overall system

**Cons:**
- ❌ Takes longer to implement
- ❌ Requires thorough testing
- ❌ Higher risk during deployment

**Time Estimate:** _[Y hours/days]_

**Interruption Cost:**
- Sprint tasks delayed: _[List affected tasks]_
- Team members required: _[Number and roles]_
- Sprint completion risk: _[High/Medium/Low]_

## 🔄 Cascading Effects Analysis

### If we do Option 1 (Hotfix):
- **Immediate:** _[What happens right after deployment]_
- **Next Sprint:** _[Follow-up work required]_
- **Long-term:** _[Technical debt and maintenance impact]_

### If we do Option 2 (Proper Fix):
- **Immediate:** _[Impact on current sprint and deliverables]_
- **Next Sprint:** _[Cleaner state, no follow-up needed]_
- **Long-term:** _[System improvements and prevention]_

### If we do nothing:
- **Next 1 hour:** _[Escalation scenario]_
- **Next 24 hours:** _[Full impact scenario]_
- **Business impact:** _[Reputation, revenue, compliance]_

## 🤖 AI Recommendation

**Recommended Approach:** _[Option 1 or 2]_

**Rationale:**
_[Detailed explanation of why this option is recommended based on:]
- Severity and urgency of the issue
- Available resources and expertise
- Current sprint commitments
- Long-term system health
- Business priorities]_

## 👥 Human Decision Framework

**Key Questions for Leadership:**

1. **Business Priority:** Is fixing this issue more important than current sprint deliverables?
2. **Resource Availability:** Do we have the right people available now?
3. **Risk Tolerance:** Can we accept the risk of a quick fix vs. proper solution?
4. **Customer Communication:** What do we need to tell customers and when?
5. **Compliance/Legal:** Are there regulatory implications to consider?

**Decision Checklist:**
- [ ] Incident commander assigned
- [ ] Stakeholders notified
- [ ] Customer communication plan
- [ ] Resource allocation confirmed
- [ ] Success criteria defined
- [ ] Rollback plan prepared

## 📋 Next Steps

1. **Immediate (Next 30 min):**
   - [ ] Review this analysis with incident commander
   - [ ] Make go/no-go decision
   - [ ] Assign resources

2. **Short-term (Next 2 hours):**
   - [ ] Begin implementation of chosen option
   - [ ] Set up monitoring and alerts
   - [ ] Prepare customer communication

3. **Follow-up:**
   - [ ] Post-mortem scheduled
   - [ ] Lessons learned documented
   - [ ] Prevention measures identified
"""

    def update_index(self, *, print_summary: bool = True) -> None:
        index_data: dict[str, Any] = {
            "last_updated": clock.now(env=self.env).isoformat(),
            "total_items": 0,
            "by_severity": {"P0": [], "P1": [], "P2": [], "P3": [], "P4": []},
            "by_category": {"bugs": [], "wildcards": [], "work-items": []},
            "items": [],
        }

        for category in ["bugs", "wildcards", "work-items"]:
            category_dir = self.backlog_dir / category
            if not category_dir.exists():
                continue

            for issue_dir in category_dir.iterdir():
                if not issue_dir.is_dir():
                    continue

                readme_path = issue_dir / "README.md"
                if not readme_path.exists():
                    continue

                issue_info = self._parse_front_matter(readme_path)
                if not issue_info:
                    continue

                issue_info["id"] = issue_dir.name
                issue_info["path"] = str(issue_dir.relative_to(self.project_root))

                triage_path = issue_dir / "triage.md"
                issue_info["has_triage"] = triage_path.exists()

                index_data["items"].append(issue_info)
                index_data["by_category"][category].append(issue_info["id"])

                severity = issue_info.get("severity", "P2")
                if severity in index_data["by_severity"]:
                    index_data["by_severity"][severity].append(issue_info["id"])

                index_data["total_items"] += 1

        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        index_data["items"].sort(key=lambda x: (severity_order.get(x.get("severity", "P2"), 2), x.get("created", "")))

        self.backlog_dir.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
        if print_summary:
            print(f"📊 Updated backlog index: {index_data['total_items']} items")

    def _parse_front_matter(self, file_path: Path) -> dict[str, Any] | None:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.startswith("---"):
            return None

        end_marker = content.find("---", 3)
        if end_marker == -1:
            return None

        front_matter = content[3:end_marker].strip()

        result: dict[str, Any] = {}
        for line in front_matter.split("\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key:
                result[key] = value
        return result
