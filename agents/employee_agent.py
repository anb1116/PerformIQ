from datetime import date, datetime
from typing import Dict

from agents.llm_config import ask_flash

try:
    from agents.data_agent import ALL_EMPLOYEES, TEAM_AVERAGES, DataAggregatorAgent
except ImportError:
    from data_agent import ALL_EMPLOYEES, TEAM_AVERAGES, DataAggregatorAgent


class EmployeeCoachAgent:
    def __init__(self):
        self.data_agent = DataAggregatorAgent()

    def generate_self_assessment(self, employee_id: str) -> str:
        employee_data = self.data_agent.load_employee(employee_id)
        scores = self.data_agent.get_performance_score(employee_data)
        profile_summary = self.data_agent.generate_profile_summary(
            employee_data, scores, TEAM_AVERAGES
        )

        system_prompt = (
            "You are a career coach helping an employee write their self-assessment "
            "for their performance review. Write in first person (I did, I achieved, I contributed). "
            "Be specific, confident but honest. Use actual metrics provided. "
            "Sound human, not robotic. 150 words max."
        )
        user_prompt = (
            "Help me write a self-assessment based on my actual work this quarter:\n\n"
            f"{profile_summary}\n\n"
            "Write it in this format:\n\n"
            "THIS QUARTER I:\n"
            "[3-4 bullet points of achievements with specific numbers]\n\n"
            "I AM PROUD OF:\n"
            "[1-2 sentences about biggest contribution]\n\n"
            "I WANT TO IMPROVE IN:\n"
            "[1-2 honest areas of growth]\n\n"
            "MY GOAL NEXT QUARTER:\n"
            "[1 specific goal]"
        )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        drafted = ask_flash(prompt)
        if drafted and (not drafted.startswith("Error:")) and drafted.strip():
            return drafted.strip()

        jira = employee_data.get("jira_data", {})
        github = employee_data.get("github_data", {})
        confluence = employee_data.get("confluence_data", {})
        hr = employee_data.get("hr_data", {})
        return (
            "THIS QUARTER I:\n"
            f"- I closed {jira.get('tickets_closed', 0)} Jira tickets and maintained "
            f"{jira.get('on_time_delivery_percent', 0)}% on-time delivery.\n"
            f"- I contributed {github.get('total_commits', 0)} commits, merged "
            f"{github.get('prs_merged', 0)} PRs, and reviewed {github.get('prs_reviewed', 0)} PRs.\n"
            f"- I supported team knowledge sharing by creating {confluence.get('docs_created', 0)} "
            f"and updating {confluence.get('docs_updated', 0)} Confluence docs.\n"
            f"- I completed {hr.get('goals_completed', 0)} of {hr.get('goals_set', 0)} goals this quarter.\n\n"
            "I AM PROUD OF:\n"
            "I am most proud of balancing delivery and quality while actively supporting peers. "
            "I stayed consistent across execution and collaboration.\n\n"
            "I WANT TO IMPROVE IN:\n"
            "I want to improve documentation depth and make my project updates even more proactive. "
            "I also want to reduce avoidable rework by tightening planning quality.\n\n"
            "MY GOAL NEXT QUARTER:\n"
            "I will improve cross-team execution by publishing one high-impact technical note per sprint."
        )

    def get_progress_alert(self, employee_id: str) -> dict:
        employee_data = self.data_agent.load_employee(employee_id)
        hr = employee_data.get("hr_data", {})
        goals_set = hr.get("goals_set", 0)
        goals_completed = hr.get("goals_completed", 0)
        ratio = (goals_completed / goals_set) if goals_set else 0.0

        if ratio < 0.5:
            status = "HIGH RISK"
        elif ratio < 0.75:
            status = "MEDIUM RISK"
        else:
            status = "ON TRACK"

        summary = self.data_agent.data_dir / "company_summary.json"
        deadline_text = "upcoming"
        if summary.exists():
            import json

            review_deadline = json.loads(summary.read_text(encoding="utf-8")).get(
                "review_deadline"
            )
            if review_deadline:
                deadline = datetime.strptime(review_deadline, "%Y-%m-%d").date()
                days_left = (deadline - date.today()).days
                deadline_text = f"{max(days_left, 0)} days"

        message = (
            f"You have completed {goals_completed}/{goals_set} goals. "
            f"Review deadline is in {deadline_text}. Consider discussing with your manager."
        )

        return {"status": status, "message": message}

    def explain_rating(self, employee_id: str, given_rating: float) -> str:
        employee_data = self.data_agent.load_employee(employee_id)
        scores = self.data_agent.get_performance_score(employee_data)
        profile_summary = self.data_agent.generate_profile_summary(
            employee_data, scores, TEAM_AVERAGES
        )

        system_prompt = (
            "You are a supportive HR coach explaining a performance rating to an employee. "
            "Be empathetic, clear, and constructive. Never be harsh. Always end on a positive note."
        )
        user_prompt = (
            f"Explain to the employee why they received a rating of {given_rating}/10.0\n"
            f"based on their performance data:\n{profile_summary}\n"
            "Use specific data points to justify the rating. 100 words max."
        )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        explanation = ask_flash(prompt)
        if explanation and not explanation.startswith("Error:"):
            return explanation

        return (
            f"You received a rating of {given_rating}/10.0 based on a blend of outcomes, quality, and team impact. "
            f"Your delivery and execution were supported by clear metrics such as "
            f"{employee_data.get('jira_data', {}).get('tickets_closed', 0)} tickets closed and "
            f"{employee_data.get('jira_data', {}).get('on_time_delivery_percent', 0)}% on-time delivery, along with "
            f"{employee_data.get('github_data', {}).get('total_commits', 0)} commits. "
            "At the same time, there are opportunities to improve consistency in areas with lower scores. "
            "You have a strong base and clear path to grow further next quarter."
        )

    @staticmethod
    def _ordinal(n: int) -> str:
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def get_my_dashboard_data(self, employee_id: str) -> dict:
        employee_data = self.data_agent.load_employee(employee_id)
        my_scores = self.data_agent.get_performance_score(employee_data)
        all_scores = {
            emp_id: self.data_agent.get_performance_score(emp)
            for emp_id, emp in ALL_EMPLOYEES.items()
        }

        ranking = sorted(
            all_scores.items(), key=lambda item: item[1].get("overall_score", 0.0), reverse=True
        )
        rank_position = next(
            (idx + 1 for idx, (emp_id, _) in enumerate(ranking) if emp_id == employee_id), 0
        )
        team_rank = f"{self._ordinal(rank_position)} out of {len(ranking)}"

        score_map = {
            "delivery_score": "Delivery",
            "quality_score": "Quality",
            "collaboration_score": "Collaboration",
            "documentation_score": "Documentation",
            "goal_score": "Goals",
        }
        top_key = max(score_map, key=lambda k: my_scores.get(k, 0.0))
        low_key = min(score_map, key=lambda k: my_scores.get(k, 0.0))

        goal_status = self.get_progress_alert(employee_id)["status"]
        invisible = self.data_agent.detect_invisible_contributions(employee_data)

        return {
            "name": employee_data.get("name", ""),
            "overall_score": my_scores.get("overall_score", 0.0),
            "scores": my_scores,
            "team_rank": team_rank,
            "goal_status": goal_status,
            "top_strength": score_map[top_key],
            "area_to_improve": score_map[low_key],
            "invisible_contributions": invisible,
            "review_status": employee_data.get("review_status", "pending"),
        }


if __name__ == "__main__":
    agent = EmployeeCoachAgent()
    print(agent.generate_self_assessment("EMP001"))
    print(agent.get_progress_alert("EMP001"))
