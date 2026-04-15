from typing import Dict, List, Tuple
from agents.llm_config import ask_flash, ask_pro

try:
    from agents.data_agent import DataAggregatorAgent, TEAM_AVERAGES
except ImportError:
    from data_agent import DataAggregatorAgent, TEAM_AVERAGES


class ManagerAssistantAgent:
    def __init__(self):
        self.data_agent = DataAggregatorAgent()

    def suggest_rating(self, scores: dict) -> tuple:
        overall = float(scores.get("overall_score", 0.0))
        if overall >= 9.0:
            return 9.5, "Exceptional"
        if overall >= 7.5:
            return 8.5, "Exceeds Expectations"
        if overall >= 6.0:
            return 7.0, "Meets Expectations"
        if overall >= 4.0:
            return 5.0, "Below Expectations"
        return 3.0, "Needs Improvement"

    def generate_draft_review(self, employee_id: str) -> dict:
        employee_data = self.data_agent.load_employee(employee_id)
        scores = self.data_agent.get_performance_score(employee_data)
        profile_summary = self.data_agent.generate_profile_summary(
            employee_data, scores, TEAM_AVERAGES
        )
        bias_risk = self.data_agent.detect_bias_risk(employee_data, scores)
        invisible_contributions = self.data_agent.detect_invisible_contributions(employee_data)
        recommended_rating, recommended_band = self.suggest_rating(scores)

        system_prompt = (
            "You are an expert HR performance review writer. You write fair, "
            "data-backed, constructive performance reviews. You never use vague language. "
            "You always cite specific metrics and achievements. You are balanced - "
            "you mention strengths and areas of improvement. You write in professional "
            "but warm tone. Keep reviews between 150-200 words."
        )
        user_prompt = (
            "Write a performance review for the following employee based on their "
            "actual work data. Use specific numbers and metrics from the data provided.\n\n"
            f"{profile_summary}\n\n"
            f"Invisible contributions detected: {invisible_contributions}\n\n"
            "Write the review in this format:\n\n"
            "PERFORMANCE SUMMARY:\n"
            "[2-3 sentences overall assessment with specific metrics]\n\n"
            "KEY STRENGTHS:\n"
            "[3 bullet points with specific data evidence]\n\n"
            "AREAS FOR IMPROVEMENT:\n"
            "[2 bullet points with constructive suggestions]\n\n"
            "RECOMMENDED RATING: [X.X / 10.0]\n"
            "RECOMMENDED BAND: [Exceptional/Exceeds Expectations/Meets Expectations/Below Expectations]"
        )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        review_text = ask_pro(prompt)

        if (not review_text) or review_text.startswith("Error:"):
            review_text = (
                "PERFORMANCE SUMMARY:\n"
                f"{employee_data['name']} delivered an overall score of {scores['overall_score']:.1f}/10 "
                f"for {employee_data['review_period']}, with strong delivery ({scores['delivery_score']:.1f}) "
                f"and quality ({scores['quality_score']:.1f}). The employee closed "
                f"{employee_data['jira_data']['tickets_closed']} Jira tickets with "
                f"{employee_data['jira_data']['on_time_delivery_percent']}% on-time delivery and contributed "
                f"{employee_data['github_data']['total_commits']} commits.\n\n"
                "KEY STRENGTHS:\n"
                f"- Strong execution with {employee_data['jira_data']['tickets_closed']} tickets closed.\n"
                f"- Solid engineering output with {employee_data['github_data']['prs_merged']} merged PRs and "
                f"{employee_data['github_data']['prs_reviewed']} PR reviews.\n"
                f"- Knowledge sharing through {employee_data['confluence_data']['docs_created']} docs created and "
                f"{employee_data['confluence_data']['docs_updated']} updates.\n\n"
                "AREAS FOR IMPROVEMENT:\n"
                "- Improve cross-functional documentation visibility and consistency.\n"
                "- Continue focusing on preventive quality practices to lower rework risk.\n\n"
                f"RECOMMENDED RATING: {recommended_rating:.1f} / 10.0\n"
                f"RECOMMENDED BAND: {recommended_band}"
            )

        return {
            "review_text": review_text,
            "recommended_rating": recommended_rating,
            "recommended_band": recommended_band,
            "bias_risk": bias_risk,
            "invisible_contributions": invisible_contributions,
            "profile_summary": profile_summary,
        }

    def generate_nudge_message(self, employee_id: str, days_remaining: int) -> str:
        employee_data = self.data_agent.load_employee(employee_id)
        employee_name = employee_data.get("name", "the employee")
        tickets_closed = employee_data.get("jira_data", {}).get("tickets_closed", 0)
        commits = employee_data.get("github_data", {}).get("total_commits", 0)

        system_prompt = (
            "You are a friendly HR assistant. Write short, warm, non-pushy reminder "
            "messages to managers about completing performance reviews. Max 3 sentences."
        )
        user_prompt = (
            f"Write a reminder to the manager of {employee_name} that their performance "
            f"review is due in {days_remaining} days. The employee has {tickets_closed} Jira "
            f"tickets closed and {commits} GitHub commits this quarter - good data is available "
            "to support the review."
        )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        nudge = ask_flash(prompt)
        if nudge and not nudge.startswith("Error:"):
            return nudge

        return (
            f"Friendly reminder: {employee_name}'s performance review is due in {days_remaining} days. "
            f"You already have strong input data this quarter ({tickets_closed} Jira tickets closed, "
            f"{commits} GitHub commits), so wrapping this up should be straightforward."
        )


if __name__ == "__main__":
    agent = ManagerAssistantAgent()
    result = agent.generate_draft_review("EMP001")
    print(result["review_text"])
    print("Bias Risk:", result["bias_risk"])
    print("Invisible Contributions:", result["invisible_contributions"])
