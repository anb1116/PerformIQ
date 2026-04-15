from collections import defaultdict
from typing import Any

from agents.data_agent import DataAggregatorAgent


def _to_10_rating(raw_rating: float) -> float:
    value = float(raw_rating or 0.0)
    if 0.0 < value <= 5.0:
        value *= 2.0
    return round(max(0.0, min(10.0, value)), 2)


def build_employee_dataset() -> dict:
    """Single standardized dataset used by all analytics actions."""
    agent = DataAggregatorAgent()
    employees = agent.get_all_employees()
    if not employees:
        return {}

    reviews = []
    ratings = []
    managers = defaultdict(lambda: {"manager": "", "team_size": 0, "employees": []})

    for emp in employees:
        emp_id = emp.get("employee_id", "")
        name = emp.get("name", "Unknown")
        manager = emp.get("manager_name") or emp.get("manager") or "Unknown"
        status = emp.get("review_status", "pending")
        submitted = status in ("completed", "approved_by_hr")
        scores = agent.get_performance_score(emp)
        bias = agent.detect_bias_risk(emp, scores) if submitted else {"risk_level": "NONE", "message": "Review not submitted"}
        hr = emp.get("hr_data", {})
        jira = emp.get("jira_data", {})
        github = emp.get("github_data", {})

        source_rating = emp.get("final_rating", None)
        if source_rating is None:
            source_rating = hr.get("last_rating", 0.0)
        mgr_rating = _to_10_rating(source_rating) if submitted else None
        gap = round(scores.get("overall_score", 0.0) - mgr_rating, 2) if submitted and mgr_rating is not None else 0.0
        goals_set = hr.get("goals_set", 0)
        goals_done = hr.get("goals_completed", 0)
        goal_completion = round((goals_done / goals_set), 3) if goals_set else 0.0
        productivity_index = round(
            jira.get("tickets_closed", 0) * 0.55
            + github.get("total_commits", 0) * 0.06
            + github.get("prs_merged", 0) * 1.0
            + github.get("prs_reviewed", 0) * 0.35,
            2,
        )
        weakest_dimension = min(
            [
                ("delivery", scores.get("delivery_score", 0.0)),
                ("quality", scores.get("quality_score", 0.0)),
                ("collaboration", scores.get("collaboration_score", 0.0)),
                ("documentation", scores.get("documentation_score", 0.0)),
                ("goals", scores.get("goal_score", 0.0)),
            ],
            key=lambda x: x[1],
        )

        row = {
            "employee_id": emp_id,
            "name": name,
            "manager": manager,
            "status": status,
            "submitted_review": submitted,
            "overall_score": float(scores.get("overall_score", 0.0)),
            "manager_rating": mgr_rating,
            "rating_gap": gap,
            "bias_risk": bias.get("risk_level", "LOW"),
            "bias_message": bias.get("message", ""),
            "goal_completion": goal_completion,
            "productivity_index": productivity_index,
            "weakest_dimension": weakest_dimension[0],
            "weakest_value": float(weakest_dimension[1]),
        }
        reviews.append(
            {
                "employee_id": emp_id,
                "status": status,
                "review_text": emp.get("review_text", ""),
                "hr_approved": bool(emp.get("hr_approved", False)),
            }
        )
        ratings.append(
            {
                "employee_id": emp_id,
                "manager_rating": mgr_rating,
                "data_score": row["overall_score"],
                "rating_gap": gap,
            }
        )
        managers[manager]["manager"] = manager
        managers[manager]["team_size"] += 1
        managers[manager]["employees"].append(row)

    return {
        "employees": employees,
        "reviews": reviews,
        "ratings": ratings,
        "managers": dict(managers),
        "records": [m for mgr in managers.values() for m in mgr["employees"]],
    }


def _base_snapshot(data: dict) -> dict:
    records = data.get("records", [])
    total = len(records)
    completed = sum(1 for r in records if r.get("status") == "completed")
    pending = total - completed
    avg_score = round(sum(r.get("overall_score", 0.0) for r in records) / total, 2) if total else 0.0
    return {
        "total_employees": total,
        "completed_reviews": completed,
        "pending_reviews": pending,
        "avg_score": avg_score,
    }


def bias_hotspots(data: dict) -> dict:
    rows = sorted(
        [
            r
            for r in data.get("records", [])
            if r.get("submitted_review") and r.get("bias_risk") in ("HIGH", "MEDIUM")
        ],
        key=lambda x: (0 if x.get("bias_risk") == "HIGH" else 1, -abs(x.get("rating_gap", 0.0))),
    )
    return {
        "title": "Bias Hotspots",
        "insights": [
            {
                "employee": r["name"],
                "employee_id": r["employee_id"],
                "manager": r["manager"],
                "risk": r["bias_risk"],
                "rating_gap": r["rating_gap"],
                "message": r["bias_message"],
            }
            for r in rows[:10]
        ],
        "recommendations": [
            "Review HIGH risk cases first with calibration panel.",
            "Require evidence-backed notes for any rating-gap above 1.0.",
        ],
    }


def under_rated_candidates(data: dict) -> dict:
    rows = sorted(
        [r for r in data.get("records", []) if r.get("submitted_review") and r.get("rating_gap", 0.0) > 0.8],
        key=lambda x: x.get("rating_gap", 0.0),
        reverse=True,
    )
    return {
        "title": "Under-Rated Candidates",
        "insights": [
            {
                "employee": r["name"],
                "employee_id": r["employee_id"],
                "data_score": r["overall_score"],
                "manager_rating": r["manager_rating"],
                "gap": r["rating_gap"],
            }
            for r in rows[:10]
        ],
        "recommendations": [
            "Discuss top 3 candidates in calibration.",
            "Adjust ratings where evidence consistently supports higher scores.",
        ],
    }


def productivity_leaders(data: dict) -> dict:
    rows = sorted(data.get("records", []), key=lambda x: x.get("productivity_index", 0.0), reverse=True)
    return {
        "title": "Productivity Leaders",
        "insights": [
            {
                "employee": r["name"],
                "employee_id": r["employee_id"],
                "manager": r["manager"],
                "productivity_index": r["productivity_index"],
                "status": r["status"],
            }
            for r in rows[:10]
        ],
        "recommendations": [
            "Use leaders as benchmarks for process playbooks.",
            "Capture repeatable execution practices in team docs.",
        ],
    }


def coaching_priorities(data: dict) -> dict:
    rows = sorted(
        [r for r in data.get("records", []) if r.get("weakest_value", 10.0) < 6.2],
        key=lambda x: x.get("weakest_value", 10.0),
    )
    return {
        "title": "Coaching Priorities",
        "insights": [
            {
                "employee": r["name"],
                "employee_id": r["employee_id"],
                "weakest_dimension": r["weakest_dimension"],
                "score": r["weakest_value"],
            }
            for r in rows[:10]
        ],
        "recommendations": [
            "Assign targeted development plans by weakest dimension.",
            "Set 30-day improvement checkpoints with manager accountability.",
        ],
    }


def priority_queue(data: dict) -> dict:
    rows = []
    for r in data.get("records", []):
        if r.get("status") == "completed":
            continue
        risk_weight = 3.0 if r.get("bias_risk") == "HIGH" else 2.0 if r.get("bias_risk") == "MEDIUM" else 1.0
        urgency = round((risk_weight * 2.2) + abs(r.get("rating_gap", 0.0)) + ((1.0 - r.get("goal_completion", 0.0)) * 2.0), 2)
        rows.append({**r, "urgency_score": urgency})
    rows.sort(key=lambda x: x["urgency_score"], reverse=True)
    return {
        "title": "Review Priority Queue",
        "insights": [
            {
                "employee": r["name"],
                "employee_id": r["employee_id"],
                "manager": r["manager"],
                "urgency_score": r["urgency_score"],
                "risk": r["bias_risk"],
            }
            for r in rows[:10]
        ],
        "recommendations": [
            "Complete top urgency reviews first to reduce deadline + fairness risk.",
            "Escalate top 3 unresolved items to HR lead.",
        ],
    }


def manager_risk_scorecard(data: dict) -> dict:
    score_rows = []
    for manager, info in data.get("managers", {}).items():
        team = [r for r in info.get("employees", []) if r.get("submitted_review")]
        size = len(team) or 1
        if not team:
            continue
        high = sum(1 for r in team if r.get("bias_risk") == "HIGH")
        medium = sum(1 for r in team if r.get("bias_risk") == "MEDIUM")
        avg_gap = round(sum(abs(r.get("rating_gap", 0.0)) for r in team) / size, 2)
        risk_score = round((high * 3.0) + (medium * 1.5) + (avg_gap * 1.2), 2)
        score_rows.append(
            {
                "manager": manager,
                "team_size": len(team),
                "high_bias_count": high,
                "medium_bias_count": medium,
                "avg_gap": avg_gap,
                "risk_score": risk_score,
            }
        )
    score_rows.sort(key=lambda x: x["risk_score"], reverse=True)
    return {
        "title": "Manager Risk Scorecard",
        "insights": score_rows,
        "recommendations": [
            "Start calibration reviews with highest risk managers.",
            "Track manager-level gap trend weekly to verify interventions.",
        ],
    }


def weekly_digest(data: dict) -> dict:
    snapshot = _base_snapshot(data)
    bias = bias_hotspots(data).get("insights", [])[:3]
    underr = under_rated_candidates(data).get("insights", [])[:3]

    deterministic = {
        "title": "Weekly Digest",
        "insights": [
            {
                "snapshot": snapshot,
                "top_bias_cases": bias,
                "top_underrated_cases": underr,
            }
        ],
        "recommendations": [
            "Close high urgency pending reviews.",
            "Calibrate top under-rated and high-bias profiles.",
            "Push coaching plans for low-score dimensions.",
        ],
    }
    return deterministic


def rebalance_recommendations(data: dict) -> dict:
    queue = priority_queue(data).get("insights", [])
    load = defaultdict(int)
    for row in queue:
        load[row.get("manager", "Unknown")] += 1
    if not load:
        return {"title": "Rebalance Recommendations", "insights": [], "recommendations": ["No pending reviews to rebalance."]}

    managers = sorted(load.items(), key=lambda x: x[1], reverse=True)
    heavy, light = managers[0], managers[-1]
    recs = []
    if heavy[1] - light[1] > 1:
        recs.append(f"Shift one high urgency review from {heavy[0]} to {light[0]}.")
    recs.append("Keep queue sorted by urgency and bias risk.")
    return {
        "title": "Rebalance Recommendations",
        "insights": [{"manager_load": dict(load)}],
        "recommendations": recs,
    }


def manager_bias_explainer(data: dict) -> dict:
    manager_rows = []
    for manager, info in data.get("managers", {}).items():
        team = [r for r in info.get("employees", []) if r.get("submitted_review")]
        if not team:
            continue
        deviations = []
        affected = []
        for r in team:
            mgr = r.get("manager_rating")
            if mgr is None:
                continue
            mgr_10 = float(mgr)
            perf_10 = float(r.get("overall_score", 0.0))
            if perf_10 <= 0:
                continue
            dev_pct = round(((perf_10 - mgr_10) / perf_10) * 100, 2)
            deviations.append(dev_pct)
            if dev_pct > 12:
                affected.append(r.get("name", "Unknown"))
        if not deviations:
            continue
        avg_dev = round(sum(deviations) / len(deviations), 2)
        sev = "High" if avg_dev > 20 else "Medium" if avg_dev > 10 else "Low"
        statement = (
            f"Manager {manager} is underrating high performers by {avg_dev}%"
            if avg_dev > 0
            else f"Manager {manager} is overrating by {abs(avg_dev)}%"
        )
        manager_rows.append(
            {
                "manager": manager,
                "deviation_percent": avg_dev,
                "affected_employees": affected,
                "severity": sev,
                "statement": statement,
            }
        )
    manager_rows.sort(key=lambda x: abs(x.get("deviation_percent", 0.0)), reverse=True)
    return {
        "title": "Manager Bias Explainer",
        "insights": manager_rows[:6],
        "recommendations": [
            "Start calibration with High severity managers first.",
            "Ask for evidence-backed review notes where deviation is > 10%.",
        ],
    }


def invisible_top_performer_detection(data: dict) -> dict:
    hidden = []
    for r in data.get("records", []):
        if not r.get("submitted_review"):
            continue
        mgr = r.get("manager_rating")
        if mgr is None:
            continue
        mgr_10 = float(mgr)
        perf_10 = float(r.get("overall_score", 0.0))
        if perf_10 >= 7.5 and (perf_10 - mgr_10) >= 1.4:
            hidden.append(
                {
                    "employee": r.get("name", "Unknown"),
                    "employee_id": r.get("employee_id", ""),
                    "manager": r.get("manager", "Unknown"),
                    "performance_score": perf_10,
                    "manager_score_10": round(mgr_10, 2),
                    "statement": (
                        f"{r.get('name','Employee')} is a hidden high performer being under-recognized"
                    ),
                }
            )
    hidden.sort(key=lambda x: (x["performance_score"] - x["manager_score_10"]), reverse=True)
    return {
        "title": "Invisible Top Performer Detection",
        "insights": hidden[:8],
        "recommendations": [
            "Escalate hidden performers in calibration and talent review.",
            "Prioritize recognition and stretch opportunities for these employees.",
        ],
    }


def weekly_hr_action_plan(data: dict) -> dict:
    bias = manager_bias_explainer(data).get("insights", [])
    queue = priority_queue(data).get("insights", [])
    underr = under_rated_candidates(data).get("insights", [])

    top_bias = bias[0] if bias else None
    top_pending = queue[0] if queue else None
    top_under = underr[0] if underr else None

    actions = []
    if top_bias:
        actions.append(
            f"Run calibration with {top_bias['manager']} first ({top_bias['severity']} severity, {top_bias['deviation_percent']}% deviation)."
        )
    if top_pending:
        actions.append(
            f"Close highest urgency pending review: {top_pending['employee']} ({top_pending['employee_id']}) with manager {top_pending['manager']}."
        )
    if top_under:
        actions.append(
            f"Re-evaluate under-rated employee {top_under['employee']} (gap {top_under['gap']}) before final rating lock."
        )

    while len(actions) < 3:
        actions.append("Audit manager notes quality for evidence-backed ratings.")

    return {
        "title": "Weekly HR Action Plan",
        "insights": ["Top Actions This Week:"] + [f"{i+1}. {a}" for i, a in enumerate(actions[:3])],
        "recommendations": [
            "Track action closure in next HR weekly review.",
            "Recompute risk scorecard after actions are completed.",
        ],
    }


def run_analysis(action: str, data: dict, **kwargs: Any):
    if not data:
        return {"error": "No data available"}

    if action == "bias_hotspots":
        return bias_hotspots(data)
    if action == "under_rated_candidates":
        return under_rated_candidates(data)
    if action == "productivity_leaders":
        return productivity_leaders(data)
    if action == "coaching_priorities":
        return coaching_priorities(data)
    if action == "priority_queue":
        return priority_queue(data)
    if action == "manager_risk_scorecard":
        return manager_risk_scorecard(data)
    if action == "weekly_digest":
        return weekly_digest(data)
    if action == "rebalance_recommendations":
        return rebalance_recommendations(data)
    if action == "manager_bias_explainer":
        return manager_bias_explainer(data)
    if action == "weekly_hr_action_plan":
        return weekly_hr_action_plan(data)
    if action == "invisible_top_performer_detection":
        return invisible_top_performer_detection(data)
    return {"error": f"Unknown action: {action}"}


class IntelligenceAgent:
    """Compatibility wrapper for existing app references."""

    def answer_query(self, query: str) -> str:
        data = build_employee_dataset()
        q = (query or "").lower()
        if "bias" in q:
            res = run_analysis("bias_hotspots", data)
        elif "underrated" in q or "rating gap" in q:
            res = run_analysis("under_rated_candidates", data)
        elif "product" in q or "throughput" in q:
            res = run_analysis("productivity_leaders", data)
        elif "coach" in q or "improve" in q:
            res = run_analysis("coaching_priorities", data)
        elif "priority" in q or "urgent" in q:
            res = run_analysis("priority_queue", data)
        else:
            res = run_analysis("weekly_digest", data)
        return str(res)

    def generate_weekly_digest(self):
        return run_analysis("weekly_digest", build_employee_dataset())

    def manager_risk_scorecard(self):
        return run_analysis("manager_risk_scorecard", build_employee_dataset()).get("insights", [])

    def review_priority_queue(self):
        return run_analysis("priority_queue", build_employee_dataset()).get("insights", [])

    def team_rebalance_optimizer(self):
        result = run_analysis("rebalance_recommendations", build_employee_dataset())
        return [
            {
                "recommendation": rec,
                "reason": "Auto-generated by rebalance engine",
                "from_manager": "Auto",
                "to_manager": "Auto",
                "estimated_impact": "Medium",
            }
            for rec in result.get("recommendations", [])
        ]
