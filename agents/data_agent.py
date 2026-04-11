import json
import sys
from pathlib import Path


class DataAggregatorAgent:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / "data"

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _safe_div(numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def load_employee(self, employee_id: str) -> dict:
        file_path = self.data_dir / f"{employee_id}.json"
        return json.loads(file_path.read_text(encoding="utf-8"))

    def get_performance_score(self, employee_data: dict) -> dict:
        jira = employee_data.get("jira_data", {})
        github = employee_data.get("github_data", {})
        confluence = employee_data.get("confluence_data", {})
        slack = employee_data.get("slack_data", {})
        hr = employee_data.get("hr_data", {})

        # Delivery: throughput + predictability + sprint consistency.
        tickets_score = self._clamp(jira.get("tickets_closed", 0) / 5.0)
        on_time_score = self._clamp(jira.get("on_time_delivery_percent", 0) / 10.0)
        velocity_score = self._clamp(jira.get("sprint_velocity_avg", 0))
        delivery_score = self._clamp(
            (tickets_score * 0.4) + (on_time_score * 0.35) + (velocity_score * 0.25)
        )

        # Quality: fewer bugs + constructive code feedback + merge quality proxy.
        bugs_penalty = self._clamp(jira.get("bugs_reported_against", 0), 0.0, 10.0)
        bugs_score = self._clamp(10.0 - bugs_penalty * 1.5)
        review_comments_score = self._clamp(github.get("code_review_comments", 0) / 4.0)
        pr_quality_ratio = self._safe_div(
            github.get("prs_merged", 0),
            github.get("prs_merged", 0) + jira.get("tickets_in_progress", 0),
        )
        pr_quality_score = self._clamp(pr_quality_ratio * 10.0)
        quality_score = self._clamp(
            (bugs_score * 0.45) + (review_comments_score * 0.3) + (pr_quality_score * 0.25)
        )

        # Collaboration: mentoring/reviews + documentation + peer appreciation.
        pr_reviews_score = self._clamp(github.get("prs_reviewed", 0) / 2.0)
        confluence_collab_score = self._clamp(
            (confluence.get("docs_created", 0) + confluence.get("docs_updated", 0)) / 3.0
        )
        kudos_score = self._clamp(
            (slack.get("kudos_received", 0) * 0.65) + (slack.get("kudos_given", 0) * 0.35)
        )
        collaboration_score = self._clamp(
            (pr_reviews_score * 0.4)
            + (confluence_collab_score * 0.35)
            + (kudos_score * 0.25)
        )

        # Documentation: confluence authoring + maintenance + engagement.
        docs_created_score = self._clamp(confluence.get("docs_created", 0) * 1.6)
        docs_updated_score = self._clamp(confluence.get("docs_updated", 0) / 1.5)
        docs_views_score = self._clamp(confluence.get("pages_viewed_by_others", 0) / 40.0)
        documentation_score = self._clamp(
            (docs_created_score * 0.4) + (docs_updated_score * 0.35) + (docs_views_score * 0.25)
        )

        # Goals: completion against set goals.
        goals_set = hr.get("goals_set", 0)
        goals_completed = hr.get("goals_completed", 0)
        goal_completion_ratio = self._safe_div(goals_completed, goals_set)
        goal_score = self._clamp(goal_completion_ratio * 10.0)

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
        score_keys = [
            "delivery_score",
            "quality_score",
            "collaboration_score",
            "documentation_score",
            "goal_score",
            "overall_score",
        ]
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

        return (
            f"{employee_data.get('name', 'Unknown')} | {employee_data.get('role', 'Unknown')} | "
            f"{employee_data.get('review_period', 'N/A')}\n\n"
            "📊 Performance Scores:\n"
            f"• Delivery: {scores['delivery_score']:.1f}/10 "
            f"(Team avg: {team_avg.get('delivery_score', 0):.1f})\n"
            f"• Quality: {scores['quality_score']:.1f}/10 "
            f"(Team avg: {team_avg.get('quality_score', 0):.1f})\n"
            f"• Collaboration: {scores['collaboration_score']:.1f}/10 "
            f"(Team avg: {team_avg.get('collaboration_score', 0):.1f})\n"
            f"• Documentation: {scores['documentation_score']:.1f}/10 "
            f"(Team avg: {team_avg.get('documentation_score', 0):.1f})\n"
            f"• Goals: {scores['goal_score']:.1f}/10 "
            f"(Team avg: {team_avg.get('goal_score', 0):.1f})\n"
            f"• OVERALL: {scores['overall_score']:.1f}/10 "
            f"(Team avg: {team_avg.get('overall_score', 0):.1f})\n\n"
            f"🎯 Goals: {hr.get('goals_completed', 0)}/{hr.get('goals_set', 0)} completed, "
            f"{hr.get('goals_in_progress', 0)} in progress\n"
            f"📅 Attendance: {hr.get('attendance_percentage', 0)}%\n"
            f"💻 GitHub: {github.get('total_commits', 0)} commits, "
            f"{github.get('prs_merged', 0)} PRs merged, {github.get('prs_reviewed', 0)} reviews\n"
            f"🎫 Jira: {jira.get('tickets_closed', 0)} tickets closed, "
            f"{jira.get('on_time_delivery_percent', 0)}% on-time delivery\n"
            f"📝 Confluence: {confluence.get('docs_created', 0)} docs created, "
            f"{confluence.get('docs_updated', 0)} updated"
        )

    def detect_bias_risk(self, employee_data: dict, scores: dict) -> dict:
        manager_rating = float(employee_data.get("hr_data", {}).get("last_rating", 0.0))
        data_score = float(scores.get("overall_score", 0.0))
        gap = round(data_score - manager_rating, 2)
        abs_gap = abs(gap)

        if abs_gap > 1.5:
            risk_level = "HIGH BIAS RISK"
            short_risk = "HIGH"
        elif abs_gap > 0.8:
            risk_level = "MEDIUM BIAS RISK"
            short_risk = "MEDIUM"
        else:
            risk_level = "LOW BIAS RISK"
            short_risk = "LOW"

        direction = "below" if gap < 0 else "above"
        message = (
            f"Manager rating {abs_gap:.1f} points {direction} data score. "
            f"{'Review recommended.' if short_risk != 'LOW' else 'No significant mismatch detected.'}"
        )

        return {
            "risk_level": short_risk,
            "message": message,
            "risk_label": risk_level,
        }

    def detect_invisible_contributions(self, employee_data: dict) -> list:
        github = employee_data.get("github_data", {})
        confluence = employee_data.get("confluence_data", {})
        slack = employee_data.get("slack_data", {})
        jira = employee_data.get("jira_data", {})

        contributions = []

        if github.get("prs_reviewed", 0) > 10:
            contributions.append("Strong peer reviewer")
        if confluence.get("docs_created", 0) > 3:
            contributions.append("Knowledge contributor")
        if slack.get("kudos_given", 0) > 4:
            contributions.append("Team motivator")
        if jira.get("collaboration_tickets", 0) > 4:
            contributions.append("Cross-team collaborator")

        return contributions


_agent_for_globals = DataAggregatorAgent()
ALL_EMPLOYEES = {}
for _employee_file in sorted(_agent_for_globals.data_dir.glob("EMP*.json")):
    _employee = json.loads(_employee_file.read_text(encoding="utf-8"))
    ALL_EMPLOYEES[_employee["employee_id"]] = _employee

TEAM_AVERAGES = _agent_for_globals.get_team_averages(list(ALL_EMPLOYEES.values()))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    agent = DataAggregatorAgent()
    emp = agent.load_employee("EMP001")
    scores = agent.get_performance_score(emp)
    team_avg = TEAM_AVERAGES
    print(agent.generate_profile_summary(emp, scores, team_avg))
    print(agent.detect_bias_risk(emp, scores))
    print(agent.detect_invisible_contributions(emp))
