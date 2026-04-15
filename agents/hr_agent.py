import json
from datetime import date, datetime
from typing import Dict, List

from agents.llm_config import ask_flash, ask_pro

try:
    from agents.data_agent import ALL_EMPLOYEES, TEAM_AVERAGES, DataAggregatorAgent
except ImportError:
    from data_agent import ALL_EMPLOYEES, TEAM_AVERAGES, DataAggregatorAgent


class HROrchestratorAgent:
    def __init__(self):
        self.data_agent = DataAggregatorAgent()
        # NOTE: Don't rely on import-time globals for "live" dashboards.
        # The Streamlit app writes JSON to disk; we should reload from disk when needed.
        self.employees = ALL_EMPLOYEES
        self.company_summary_path = self.data_agent.data_dir / "company_summary.json"

    def _get_days_left(self) -> int:
        if not self.company_summary_path.exists():
            return 0
        summary = json.loads(self.company_summary_path.read_text(encoding="utf-8"))
        deadline_str = summary.get("review_deadline")
        if not deadline_str:
            return 0
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        return max((deadline - date.today()).days, 0)

    def _employee_scores(self) -> Dict[str, dict]:
        employees = self.data_agent.get_all_employees()
        return {
            (employee.get("employee_id") or ""): self.data_agent.get_performance_score(employee)
            for employee in employees
            if employee.get("employee_id")
        }

    def get_cycle_dashboard(self) -> dict:
        employees = self.data_agent.get_all_employees()
        total = len(employees)
        completed = sum(1 for emp in employees if emp.get("review_status", "pending") in ("completed", "approved_by_hr"))
        pending = total - completed
        completion_rate = f"{round((completed / total) * 100) if total else 0}%"

        days_left = self._get_days_left()
        at_risk_reviews = []
        if days_left < 5:
            at_risk_reviews = [
                emp.get("name", "Unknown")
                for emp in employees
                if emp.get("review_status", "pending") == "pending"
            ]

        scores_by_id = {emp.get("employee_id"): self.data_agent.get_performance_score(emp) for emp in employees if emp.get("employee_id")}
        ranked = sorted(
            [(emp, scores_by_id.get(emp.get("employee_id"), {})) for emp in employees],
            key=lambda item: item[1].get("overall_score", 0.0),
            reverse=True,
        )
        high_performers = [emp.get("name", "Unknown") for emp, _ in ranked[:3]]
        needs_attention = [emp.get("name", "Unknown") for emp, _ in ranked[-2:]] if ranked else []

        bias_flags = []
        for employee in employees:
            status = employee.get("review_status", "pending")
            submitted = status in ("completed", "approved_by_hr")
            if not submitted:
                continue
            emp_id = employee.get("employee_id")
            if not emp_id:
                continue
            bias = self.data_agent.detect_bias_risk(employee, scores_by_id.get(emp_id, {}))
            if bias.get("risk_level") in ("HIGH", "MEDIUM"):
                bias_flags.append(
                    {
                        "employee": employee.get("name", "Unknown"),
                        "manager": employee.get("manager", "Unknown"),
                        "message": bias.get("message", ""),
                        "risk_level": bias.get("risk_level", ""),
                    }
                )

        avg_team_score = round(
            sum(v.get("overall_score", 0.0) for v in scores_by_id.values()) / total, 2
        ) if total else 0.0

        return {
            "total_employees": total,
            "reviews_completed": completed,
            "reviews_pending": pending,
            "completion_rate": completion_rate,
            "at_risk_reviews": at_risk_reviews,
            "high_performers": high_performers,
            "needs_attention": needs_attention,
            "bias_flags": bias_flags,
            "avg_team_score": avg_team_score,
        }

    def get_pending_reviews(self) -> list:
        pending = []
        for employee in self.employees.values():
            if employee.get("review_status", "pending") != "pending":
                continue

            # Proxy measure: newer joiners typically need longer context building.
            joining_date = datetime.strptime(employee["hr_data"]["joining_date"], "%Y-%m-%d").date()
            days_since_started = max((date.today() - joining_date).days, 0)

            sections = ["hr_data", "jira_data", "github_data", "confluence_data", "slack_data"]
            available = sum(1 for section in sections if employee.get(section))
            data_availability_score = round((available / len(sections)) * 100, 1)

            pending.append(
                {
                    "name": employee["name"],
                    "role": employee["role"],
                    "manager": employee["manager"],
                    "days_since_started": days_since_started,
                    "data_availability_score": data_availability_score,
                }
            )
        return pending

    def detect_team_bias_patterns(self) -> list:
        manager_gaps: Dict[str, List[float]] = {}
        for emp_id, employee in self.employees.items():
            scores = self.data_agent.get_performance_score(employee)
            manager_rating = self.data_agent._normalize_rating_to_10(
                employee.get("hr_data", {}).get("last_rating", 0.0)
            )
            data_score = float(scores.get("overall_score", 0.0))
            gap = data_score - manager_rating
            manager = employee.get("manager", "Unknown")
            manager_gaps.setdefault(manager, []).append(gap)

        warnings = []
        for manager, gaps in manager_gaps.items():
            if not gaps:
                continue
            avg_gap = sum(gaps) / len(gaps)
            under_rated_count = sum(1 for g in gaps if g > 0.8)
            if avg_gap > 0.8 and under_rated_count >= 2:
                warnings.append(
                    f"{manager}: ratings trend lower than performance data "
                    f"(avg gap +{avg_gap:.2f} across {len(gaps)} reviews)."
                )
            elif avg_gap < -0.8 and sum(1 for g in gaps if g < -0.8) >= 2:
                warnings.append(
                    f"{manager}: ratings trend higher than performance data "
                    f"(avg gap {avg_gap:.2f} across {len(gaps)} reviews)."
                )
        return warnings

    def generate_hr_summary_report(self) -> str:
        dashboard = self.get_cycle_dashboard()
        total = dashboard["total_employees"]
        rate = dashboard["completion_rate"].replace("%", "")
        avg_score = dashboard["avg_team_score"]
        high_performers = ", ".join(dashboard["high_performers"]) if dashboard["high_performers"] else "None"
        at_risk = (
            ", ".join(dashboard["at_risk_reviews"]) if dashboard["at_risk_reviews"] else "None"
        )
        bias_count = len(dashboard["bias_flags"])

        invisible_count = sum(
            len(self.data_agent.detect_invisible_contributions(emp))
            for emp in self.employees.values()
        )

        system_prompt = (
            "You are an HR analytics expert. Generate a concise executive summary "
            "of the team's performance review cycle. Be factual, use numbers, highlight "
            "risks and wins. Professional tone. 200 words max."
        )
        user_prompt = (
            "Generate an HR executive summary for Q1 2026 review cycle at TechNova:\n\n"
            f"Total employees: {total}\n"
            f"Completion rate: {rate}%\n"
            f"Average team performance score: {avg_score}/10\n"
            f"High performers: {high_performers}\n"
            f"At risk employees: {at_risk}\n"
            f"Bias flags raised: {bias_count}\n"
            f"Invisible contributors detected: {invisible_count}\n\n"
            "Highlight what HR should focus on this week."
        )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        summary = ask_pro(prompt)
        if summary and not summary.startswith("Error:"):
            return summary

        return (
            f"TechNova's Q1 2026 review cycle currently covers {total} employees with a "
            f"{dashboard['completion_rate']} completion rate and an average performance score of "
            f"{avg_score}/10. Top performers this cycle are {high_performers}, while "
            f"attention is needed for {', '.join(dashboard['needs_attention'])}. "
            f"There are {bias_count} high-bias-risk flags and {len(dashboard['at_risk_reviews'])} "
            "reviews at deadline risk. HR should prioritize manager follow-ups on pending reviews, "
            "validate flagged rating discrepancies, and recognize invisible contributors in final calibrations."
        )

    def get_department_breakdown(self) -> dict:
        grouped: Dict[str, List[float]] = {}
        for employee in self.employees.values():
            dept = employee.get("department", "Unknown")
            score = self.data_agent.get_performance_score(employee).get("overall_score", 0.0)
            grouped.setdefault(dept, []).append(score)

        avg_by_department = {
            dept: round(sum(scores) / len(scores), 2) for dept, scores in grouped.items() if scores
        }
        if not avg_by_department:
            return {
                "department_scores": {},
                "best_department": None,
                "worst_department": None,
            }

        best_department = max(avg_by_department, key=avg_by_department.get)
        worst_department = min(avg_by_department, key=avg_by_department.get)
        return {
            "department_scores": avg_by_department,
            "best_department": best_department,
            "worst_department": worst_department,
        }

    def generate_completion_nudge(self, manager_name: str, pending_count: int) -> str:
        days = self._get_days_left()
        system_prompt = (
            "You are an HR system sending a professional but firm reminder. "
            "Keep it under 3 sentences. Be polite but create urgency."
        )
        user_prompt = (
            f"Write a reminder to {manager_name} who has {pending_count} "
            f"pending reviews due in {days} days."
        )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        nudge = ask_flash(prompt)
        if nudge and not nudge.startswith("Error:"):
            return nudge
        return (
            f"Dear {manager_name}, this is a reminder that you have {pending_count} pending "
            f"performance reviews due in {days} days. Please complete them promptly to avoid "
            "calibration delays."
        )


if __name__ == "__main__":
    agent = HROrchestratorAgent()
    dashboard = agent.get_cycle_dashboard()
    print("Completion Rate:", dashboard["completion_rate"])
    print("Bias Flags:", dashboard["bias_flags"])
    print(agent.generate_hr_summary_report())
