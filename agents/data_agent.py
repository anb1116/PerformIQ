import json
from pathlib import Path


class DataAggregatorAgent:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / "data"
        self.company_path = self.data_dir / "company.json"

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _safe_div(numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return numerator / denominator

    @staticmethod
    def _normalize_rating_to_10(raw_rating: float) -> float:
        """Normalize legacy /5 ratings and newer /10 ratings to a common /10 scale."""
        value = float(raw_rating or 0.0)
        # Existing stored HR ratings are mostly /5; convert those to /10.
        if 0.0 < value <= 5.0:
            value = value * 2.0
        return round(max(0.0, min(10.0, value)), 2)

    def _employee_files(self):
        # Only treat canonical employee JSONs as sources of truth.
        # The dataset may include ad-hoc duplicates such as "EMP001 - Copy.json";
        # those should not be loaded into the live app.
        return sorted(
            p
            for p in self.data_dir.glob("*.json")
            if p.name != "company.json"
            and not p.name.startswith("_")
            and " - Copy" not in p.stem
        )

    def _company(self) -> dict:
        if not self.company_path.exists():
            return {}
        return json.loads(self.company_path.read_text(encoding="utf-8"))

    def load_employee(self, employee_id: str) -> dict:
        return self.get_employee_by_id(employee_id)

    def get_employee_by_id(self, employee_id: str) -> dict:
        file_path = self.data_dir / f"{employee_id}.json"
        if not file_path.exists():
            return {}
        return json.loads(file_path.read_text(encoding="utf-8"))

    def get_all_employees(self) -> list:
        # De-duplicate by employee_id and keep the latest file on disk.
        # This prevents double-counting in dashboards and alerts.
        latest_by_id: dict[str, tuple[float, dict]] = {}
        for path in self._employee_files():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            try:
                employee_id = payload.get("employee_id", "")
            except Exception:
                continue
            if not employee_id:
                continue
            if not (employee_id.startswith("EMP") or employee_id.startswith("MGR") or employee_id.startswith("HR")):
                continue
            try:
                mtime = path.stat().st_mtime
            except Exception:
                mtime = 0.0
            prev = latest_by_id.get(employee_id)
            if (prev is None) or (mtime >= prev[0]):
                latest_by_id[employee_id] = (mtime, payload)
        return [row for _, row in latest_by_id.values()]

    def get_team_members(self, manager_id: str) -> list:
        company = self._company()
        departments = company.get("departments", {})
        for dept_data in departments.values():
            if dept_data.get("head") == manager_id:
                return dept_data.get("members", [])
        return []

    def get_performance_score(self, employee_data: dict) -> dict:
        jira = employee_data.get("jira_data", {})
        github = employee_data.get("github_data", {})
        confluence = employee_data.get("confluence_data", {})
        slack = employee_data.get("slack_data", {})
        hr = employee_data.get("hr_data", {})
        crm = employee_data.get("crm_data", {})
        is_sales = "sales" in employee_data.get("department", "").lower() or bool(crm)

        tickets_score = self._clamp(jira.get("tickets_closed", 0) / 5.0)
        on_time_score = self._clamp(jira.get("on_time_delivery_percent", 0) / 10.0)
        velocity_score = self._clamp(jira.get("sprint_velocity_avg", 0))
        delivery_score = self._clamp((tickets_score * 0.4) + (on_time_score * 0.35) + (velocity_score * 0.25))

        bugs_penalty = self._clamp(jira.get("bugs_reported_against", 0), 0.0, 10.0)
        bugs_score = self._clamp(10.0 - bugs_penalty * 1.5)
        review_comments_score = self._clamp(github.get("code_review_comments", 0) / 4.0)
        pr_quality_ratio = self._safe_div(github.get("prs_merged", 0), github.get("prs_merged", 0) + jira.get("tickets_in_progress", 0))
        pr_quality_score = self._clamp(pr_quality_ratio * 10.0)
        quality_score = self._clamp((bugs_score * 0.45) + (review_comments_score * 0.3) + (pr_quality_score * 0.25))

        pr_reviews_score = self._clamp(github.get("prs_reviewed", 0) / 2.0)
        confluence_collab_score = self._clamp((confluence.get("docs_created", 0) + confluence.get("docs_updated", 0)) / 3.0)
        kudos_score = self._clamp((slack.get("kudos_received", 0) * 0.65) + (slack.get("kudos_given", 0) * 0.35))
        collaboration_score = self._clamp((pr_reviews_score * 0.4) + (confluence_collab_score * 0.35) + (kudos_score * 0.25))

        docs_created_score = self._clamp(confluence.get("docs_created", 0) * 1.6)
        docs_updated_score = self._clamp(confluence.get("docs_updated", 0) / 1.5)
        docs_views_score = self._clamp(confluence.get("pages_viewed_by_others", 0) / 40.0)
        documentation_score = self._clamp((docs_created_score * 0.4) + (docs_updated_score * 0.35) + (docs_views_score * 0.25))

        goals_set = hr.get("goals_set", 0)
        goals_completed = hr.get("goals_completed", 0)
        goal_completion_ratio = self._safe_div(goals_completed, goals_set)
        goal_score = self._clamp(goal_completion_ratio * 10.0)

        if is_sales:
            revenue_score = self._clamp(crm.get("revenue_generated", 0) / 100000.0)
            conversion_score = self._clamp(crm.get("conversion_rate", 0) / 10.0)
            deal_score = self._clamp(crm.get("deals_closed", 0) / 2.0)
            delivery_score = self._clamp((delivery_score * 0.5) + (deal_score * 0.5))
            collaboration_score = self._clamp((collaboration_score * 0.5) + (conversion_score * 0.5))
            quality_score = self._clamp((quality_score * 0.7) + (revenue_score * 0.3))

        overall_score = self._clamp(
            (delivery_score * 0.30)
            + (quality_score * 0.25)
            + (collaboration_score * 0.20)
            + (documentation_score * 0.15)
            + (goal_score * 0.10)
        )

        return {
            "delivery_score": round(delivery_score, 2),
            "quality_score": round(quality_score, 2),
            "collaboration_score": round(collaboration_score, 2),
            "documentation_score": round(documentation_score, 2),
            "goal_score": round(goal_score, 2),
            "overall_score": round(overall_score, 2),
        }

    def get_team_averages(self, all_employees: list) -> dict:
        score_keys = ["delivery_score", "quality_score", "collaboration_score", "documentation_score", "goal_score", "overall_score"]
        totals = {key: 0.0 for key in score_keys}
        count = len(all_employees)
        if count == 0:
            return totals
        for emp in all_employees:
            scores = self.get_performance_score(emp)
            for key in score_keys:
                totals[key] += scores[key]
        return {key: round(totals[key] / count, 2) for key in score_keys}

    def generate_profile_summary(self, employee_data: dict, scores: dict, team_avg: dict) -> str:
        hr = employee_data.get("hr_data", {})
        jira = employee_data.get("jira_data", {})
        github = employee_data.get("github_data", {})
        confluence = employee_data.get("confluence_data", {})
        crm = employee_data.get("crm_data", {})
        crm_line = ""
        if crm:
            crm_line = (
                f"💰 CRM: {crm.get('deals_closed', 0)} deals, revenue {crm.get('revenue_generated', 0)}, "
                f"conversion {crm.get('conversion_rate', 0)}%\n"
            )
        return (
            f"{employee_data.get('name', 'Unknown')} | {employee_data.get('role', 'Unknown')} | {employee_data.get('review_period', 'N/A')}\n\n"
            "📊 Performance Scores:\n"
            f"• Delivery: {scores['delivery_score']:.1f}/10 (Team avg: {team_avg.get('delivery_score', 0):.1f})\n"
            f"• Quality: {scores['quality_score']:.1f}/10 (Team avg: {team_avg.get('quality_score', 0):.1f})\n"
            f"• Collaboration: {scores['collaboration_score']:.1f}/10 (Team avg: {team_avg.get('collaboration_score', 0):.1f})\n"
            f"• Documentation: {scores['documentation_score']:.1f}/10 (Team avg: {team_avg.get('documentation_score', 0):.1f})\n"
            f"• Goals: {scores['goal_score']:.1f}/10 (Team avg: {team_avg.get('goal_score', 0):.1f})\n"
            f"• OVERALL: {scores['overall_score']:.1f}/10 (Team avg: {team_avg.get('overall_score', 0):.1f})\n\n"
            f"🎯 Goals: {hr.get('goals_completed', 0)}/{hr.get('goals_set', 0)} completed\n"
            f"📅 Attendance: {hr.get('attendance_percentage', 0)}%\n"
            f"💻 GitHub: {github.get('total_commits', 0)} commits, {github.get('prs_merged', 0)} PRs merged, {github.get('prs_reviewed', 0)} reviews\n"
            f"🎫 Jira: {jira.get('tickets_closed', 0)} tickets closed, {jira.get('on_time_delivery_percent', 0)}% on-time\n"
            f"📝 Confluence: {confluence.get('docs_created', 0)} docs created, {confluence.get('docs_updated', 0)} updated\n"
            f"{crm_line}"
        )

    def detect_bias_risk(self, employee_data: dict, scores: dict) -> dict:
        source_rating = employee_data.get("final_rating", None)
        if source_rating is None:
            source_rating = employee_data.get("hr_data", {}).get("last_rating", 0.0)
        manager_rating = self._normalize_rating_to_10(source_rating)
        data_score = float(scores.get("overall_score", 0.0))
        gap = abs(round(data_score - manager_rating, 2))

        if gap > 1.5:
            short_risk = "HIGH"
            risk_label = "HIGH BIAS RISK"
        elif gap > 0.8:
            short_risk = "MEDIUM"
            risk_label = "MEDIUM BIAS RISK"
        else:
            short_risk = "LOW"
            risk_label = "LOW BIAS RISK"

        notes = employee_data.get("manager_notes", "").strip()
        note_words = len([w for w in notes.split() if w])
        status = employee_data.get("review_status", "pending")
        # Only treat note-length as a bias signal when a review is actually submitted.
        feedback_bias = bool(notes) and (note_words < 20) and (status in ("completed", "approved_by_hr"))
        if feedback_bias and short_risk == "LOW":
            short_risk = "MEDIUM"
            risk_label = "MEDIUM BIAS RISK"

        direction = "above" if (manager_rating - data_score) > 0 else "below"
        msg = f"Manager rating is {gap:.1f} points {direction} data score."
        if feedback_bias:
            msg = f"{msg} FEEDBACK BIAS: manager notes are shorter than 20 words."

        return {"risk_level": short_risk, "message": msg, "risk_label": risk_label}

    def detect_invisible_contributions(self, employee_data: dict) -> list:
        github = employee_data.get("github_data", {})
        confluence = employee_data.get("confluence_data", {})
        slack = employee_data.get("slack_data", {})
        jira = employee_data.get("jira_data", {})
        crm = employee_data.get("crm_data", {})
        contributions = []
        if github.get("prs_reviewed", 0) > 8:
            contributions.append("Strong peer reviewer")
        if confluence.get("docs_created", 0) > 3:
            contributions.append("Knowledge contributor")
        if slack.get("kudos_given", 0) > 4:
            contributions.append("Team motivator")
        if jira.get("collaboration_tickets", 0) > 4:
            contributions.append("Cross-team collaborator")
        if crm and "sales" in employee_data.get("role", "").lower():
            contributions.append(f"Revenue generator ({crm.get('revenue_generated', 0)})")
        return contributions


_agent_for_globals = DataAggregatorAgent()
ALL_EMPLOYEES = {
    emp["employee_id"]: emp for emp in _agent_for_globals.get_all_employees() if emp.get("employee_id")
}
TEAM_AVERAGES = _agent_for_globals.get_team_averages(list(ALL_EMPLOYEES.values()))
