import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.data_agent import ALL_EMPLOYEES, TEAM_AVERAGES, DataAggregatorAgent
from agents.employee_agent import EmployeeCoachAgent
from agents.hr_agent import HROrchestratorAgent
from agents.manager_agent import ManagerAssistantAgent

st.set_page_config(
    page_title="PerformIQ — Agentic Performance Layer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

HR_COLOR = "#6C3483"
MANAGER_COLOR = "#1A5276"
EMP_COLOR = "#1E8449"
DANGER = "#C0392B"
WARN = "#D4AC0D"
SUCCESS = "#27AE60"

# Design tokens (aligned with modern SaaS: indigo primary, teal accent)
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --pi-primary: 230 65% 52%;
  --pi-primary-foreground: 0 0% 100%;
  --pi-accent: 172 55% 42%;
  --pi-success: 152 60% 42%;
  --pi-warning: 38 92% 50%;
  --pi-info: 200 80% 50%;
  --pi-destructive: 0 72% 51%;
  --pi-bg: 220 20% 97%;
  --pi-card: 0 0% 100%;
  --pi-foreground: 225 25% 12%;
  --pi-muted: 220 10% 46%;
  --pi-border: 220 13% 91%;
  --pi-shadow-sm: 0 1px 2px hsl(225 25% 12% / 0.05);
  --pi-shadow-md: 0 4px 16px hsl(225 25% 12% / 0.08);
  --pi-shadow-lg: 0 12px 40px hsl(225 25% 12% / 0.12);
  --pi-shadow-glow: 0 0 40px hsl(230 65% 52% / 0.15);
}
html, body, .stApp, [class*="css"] {
  font-family: 'Inter', system-ui, sans-serif !important;
}
.stApp {
  background: linear-gradient(165deg, hsl(var(--pi-bg)) 0%, hsl(220 25% 94%) 50%, hsl(220 20% 96%) 100%) !important;
  color: hsl(var(--pi-foreground)) !important;
}
h1, h2, h3, h4, h5, h6 { color: hsl(var(--pi-foreground)) !important; }
.card {
  background: hsl(var(--pi-card));
  border: 1px solid hsl(var(--pi-border));
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 12px;
  box-shadow: var(--pi-shadow-sm);
  transition: box-shadow 0.25s ease, transform 0.2s ease;
}
.card:hover { box-shadow: var(--pi-shadow-md); }
.badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.exec-box {
  background: hsl(var(--pi-card));
  border: 1px solid hsl(var(--pi-border));
  border-radius: 14px;
  padding: 16px;
  white-space: pre-wrap;
  color: hsl(var(--pi-foreground));
  box-shadow: var(--pi-shadow-sm);
}
/* ----- Login & global controls ----- */
.login-wrap { animation: piFadeUp 0.55s ease-out; }
@keyframes piFadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.login-glass {
  background: hsl(0 0% 100% / 0.88);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid hsl(var(--pi-border));
  border-radius: 20px;
  padding: 2rem 1.75rem;
  box-shadow: var(--pi-shadow-lg), var(--pi-shadow-glow);
}
.login-brand {
  text-align: center;
  margin-bottom: 0.35rem;
}
.login-brand h1 {
  font-size: 2.25rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.03em !important;
  margin: 0 !important;
  color: hsl(var(--pi-foreground)) !important;
}
.login-brand .gradient-iq {
  background: linear-gradient(135deg, hsl(var(--pi-primary)) 0%, hsl(270 55% 48%) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}
.login-tagline {
  text-align: center;
  color: hsl(var(--pi-muted));
  font-size: 0.95rem;
  margin-bottom: 0;
}
.login-role-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: hsl(var(--pi-muted));
  margin: 1.25rem 0 0.5rem 0;
}
.login-selected-pill {
  text-align: center;
  margin: 1rem 0 1.25rem;
  padding: 0.65rem 1rem;
  border-radius: 12px;
  background: hsl(230 65% 52% / 0.09);
  border: 1px solid hsl(230 65% 52% / 0.22);
  color: hsl(var(--pi-primary));
  font-weight: 600;
  font-size: 0.9rem;
}
/* Secondary buttons: light cards (fixes dark-theme black blocks) */
.stApp .stButton > button[kind="secondary"],
.stApp .stButton > button:not([kind="primary"]) {
  background: hsl(var(--pi-card)) !important;
  color: hsl(var(--pi-foreground)) !important;
  border: 1px solid hsl(var(--pi-border)) !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease !important;
  box-shadow: var(--pi-shadow-sm) !important;
}
.stApp .stButton > button[kind="secondary"]:hover,
.stApp .stButton > button:not([kind="primary"]):hover {
  border-color: hsl(var(--pi-primary) / 0.4) !important;
  box-shadow: var(--pi-shadow-md), 0 0 0 3px hsl(var(--pi-primary) / 0.1) !important;
  transform: translateY(-1px);
}
.stTextInput label {
  color: hsl(var(--pi-foreground)) !important;
  font-weight: 500 !important;
}
.stTextInput > div > div > input {
  background: hsl(var(--pi-card)) !important;
  color: hsl(var(--pi-foreground)) !important;
  border: 1px solid hsl(var(--pi-border)) !important;
  border-radius: 12px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
  border-color: hsl(var(--pi-primary)) !important;
  box-shadow: 0 0 0 3px hsl(var(--pi-primary) / 0.15) !important;
}
/* Primary = indigo gradient (not Streamlit red) */
.stApp .stButton > button[kind="primary"] {
  min-height: 48px;
  border-radius: 12px !important;
  background: linear-gradient(135deg, hsl(var(--pi-primary)) 0%, hsl(240 55% 48%) 100%) !important;
  border: none !important;
  color: hsl(var(--pi-primary-foreground)) !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  box-shadow: 0 4px 14px hsl(230 65% 52% / 0.35) !important;
  transition: transform 0.15s ease, box-shadow 0.2s ease !important;
}
.stApp .stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 22px hsl(230 65% 52% / 0.45) !important;
  transform: translateY(-1px);
}
/* Sidebar polish */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, hsl(230 30% 18%) 0%, hsl(230 28% 12%) 100%) !important;
  border-right: 1px solid hsl(0 0% 100% / 0.08);
}
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
  color: hsl(220 15% 92%) !important;
}
[data-testid="stSidebar"] .stRadio label {
  border-radius: 10px;
  padding: 0.35rem 0.5rem;
  transition: background 0.2s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: hsl(0 0% 100% / 0.06);
}
/* Metrics & alerts readability */
[data-testid="stMetricValue"] { color: hsl(var(--pi-foreground)) !important; }
[data-testid="stMetricLabel"] { color: hsl(var(--pi-muted)) !important; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_agents():
    return DataAggregatorAgent(), ManagerAssistantAgent(), EmployeeCoachAgent(), HROrchestratorAgent()


data_agent, manager_agent, employee_agent, hr_agent = init_agents()
DATA_DIR = Path(__file__).resolve().parent / "data"

MANAGER_IDS = {
    "MGR001": "Amit Desai",
    "MGR002": "Neha Kulkarni",
    "MGR003": "Kavya Reddy",
}


def load_employees():
    return [ALL_EMPLOYEES[k] for k in sorted(ALL_EMPLOYEES.keys())]


def find_employee(emp_id: str):
    return ALL_EMPLOYEES.get(emp_id)


def save_employee(emp: dict):
    path = DATA_DIR / f"{emp['employee_id']}.json"
    path.write_text(json.dumps(emp, indent=2), encoding="utf-8")
    ALL_EMPLOYEES[emp["employee_id"]] = emp


def ollama_ok():
    try:
        manager_agent.client.list()
        return True
    except Exception:
        return False


def ai_error():
    st.error("⚠️ AI engine not running. Please start Ollama and refresh.")


def login_page():
    if "login_role" not in st.session_state:
        st.session_state["login_role"] = "HR Admin"

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display: none !important; }
        section.main > div { max-width: 720px !important; margin-left: auto !important; margin-right: auto !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.35, 1])
    with center:
        st.markdown(
            """
            <div class="login-wrap">
              <div class="login-glass" style="margin-bottom: 1.25rem;">
                <div class="login-brand">
                  <h1>Perform<span class="gradient-iq">IQ</span></h1>
                </div>
                <p class="login-tagline">Intelligent performance reviews. Powered by AI.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<p class="login-role-label">Choose your role</p>', unsafe_allow_html=True)
        icons = {"HR Admin": "🏢", "Manager": "👔", "Employee": "🙋"}
        r1, r2, r3 = st.columns(3)
        for col, role in zip((r1, r2, r3), ["HR Admin", "Manager", "Employee"]):
            with col:
                if st.button(f"{icons[role]}\n{role}", key=f"role_{role}", use_container_width=True):
                    st.session_state["login_role"] = role
                    st.rerun()

        role = st.session_state["login_role"]
        st.markdown(
            f'<div class="login-selected-pill">{icons[role]} Selected: <strong>{role}</strong></div>',
            unsafe_allow_html=True,
        )

        if role == "HR Admin":
            user_id = st.text_input("HR Admin ID", placeholder="HR001", help="Demo: HR001")
        elif role == "Manager":
            user_id = st.text_input("Manager ID", placeholder="MGR001", help="MGR001–MGR003")
        else:
            user_id = st.text_input("Employee ID", placeholder="EMP001", help="EMP001–EMP010")

        password = st.text_input("Password", type="password", placeholder="Any non-empty value (demo)")

        if st.button("Sign in", type="primary", use_container_width=True):
            if not password.strip():
                st.error("Please enter a password (demo accepts any value).")
                return
            valid = False
            user_name = ""
            if role == "HR Admin" and user_id == "HR001":
                valid, user_name = True, "HR Admin"
            elif role == "Manager" and user_id in MANAGER_IDS:
                valid, user_name = True, MANAGER_IDS[user_id]
            elif role == "Employee" and user_id in ALL_EMPLOYEES:
                valid, user_name = True, ALL_EMPLOYEES[user_id]["name"]
            if not valid:
                st.error("Invalid ID. Please try again.")
                return
            st.session_state["is_logged_in"] = True
            st.session_state["role"] = role
            st.session_state["user_id"] = user_id
            st.session_state["user_name"] = user_name
            st.session_state["current_page"] = {
                "HR Admin": "📊 Overview Dashboard",
                "Manager": "📊 My Team Overview",
                "Employee": "🏠 My Dashboard",
            }[role]
            st.rerun()

        st.caption("Demo credentials: HR001 · MGR001–003 · EMP001–010 · any password")


def notification_count(role: str, user_id: str, user_name: str) -> int:
    employees = load_employees()
    if role == "HR Admin":
        return sum(1 for e in employees if e.get("review_status", "pending") != "approved_by_hr")
    if role == "Manager":
        return sum(1 for e in employees if e.get("manager") == user_name and e.get("review_status") != "completed")
    mine = find_employee(user_id)
    if not mine:
        return 0
    return 1 if not mine.get("self_assessment", "").strip() else 0


def sidebar_nav():
    role = st.session_state["role"]
    user_id = st.session_state["user_id"]
    user_name = st.session_state["user_name"]
    role_color = {"HR Admin": HR_COLOR, "Manager": MANAGER_COLOR, "Employee": EMP_COLOR}[role]
    with st.sidebar:
        st.markdown("## PerformIQ")
        st.caption(f"Welcome, {user_name}")
        st.markdown(
            f"<span class='badge' style='background:{role_color};color:white'>{role}</span>",
            unsafe_allow_html=True,
        )
        st.write(datetime.now().strftime("%d %b %Y"))
        st.divider()
        page_options = {
            "HR Admin": [
                "📊 Overview Dashboard",
                "👥 Employee Deep Dive",
                "🚨 Bias Risk Center",
                "📧 Nudge Manager",
                "📋 Reports",
            ],
            "Manager": [
                "📊 My Team Overview",
                "✍️ Write Reviews",
                "📧 Send Nudges",
                "📈 Team Analytics",
            ],
            "Employee": [
                "🏠 My Dashboard",
                "✍️ Self Assessment",
                "📊 My Progress",
                "💬 My Feedback",
            ],
        }[role]
        current = st.session_state.get("current_page", page_options[0])
        st.session_state["current_page"] = st.radio("Navigation", page_options, index=page_options.index(current))
        st.divider()
        count = notification_count(role, user_id, user_name)
        st.markdown(f"🔔 Notifications: **{count}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def hr_overview():
    st.header("HR Command Center — Q1 2026 Review Cycle")
    dashboard = hr_agent.get_cycle_dashboard()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", dashboard["total_employees"])
    c2.metric("Reviews Completed", dashboard["reviews_completed"])
    c3.metric("Completion Rate", dashboard["completion_rate"])
    c4.metric("Bias Flags", len(dashboard["bias_flags"]))
    st.progress(max(0.0, min(float(dashboard["completion_rate"].replace("%", "")) / 100, 1.0)))
    left, right = st.columns(2)
    with left:
        dept = hr_agent.get_department_breakdown().get("department_scores", {})
        if dept:
            ddf = pd.DataFrame({"Department": list(dept.keys()), "Score": list(dept.values())})
            st.plotly_chart(px.bar(ddf, x="Department", y="Score", color="Score", range_y=[0, 10]), use_container_width=True)
    with right:
        pending = [e for e in load_employees() if e.get("review_status", "pending") == "pending"]
        st.dataframe(pd.DataFrame([{"Name": e["name"], "Role": e["role"], "Manager": e["manager"]} for e in pending]), use_container_width=True, hide_index=True)
    b1, b2 = st.columns(2)
    if b1.button("📧 Send All Pending Nudges", use_container_width=True):
        by_manager = {}
        for e in load_employees():
            if e.get("review_status", "pending") == "pending":
                by_manager[e["manager"]] = by_manager.get(e["manager"], 0) + 1
        for mgr, cnt in by_manager.items():
            st.info(hr_agent.generate_completion_nudge(mgr, cnt))
        st.success("Nudges prepared.")
    if b2.button("📊 Generate Executive Report", use_container_width=True):
        if not ollama_ok():
            ai_error()
        else:
            with st.spinner("🤖 Llama is thinking..."):
                report = hr_agent.generate_hr_summary_report()
            st.markdown(f"<div class='exec-box'>{report}</div>", unsafe_allow_html=True)


def _autosave_hr_notes(emp_id: str):
    emp = find_employee(emp_id)
    if not emp:
        return
    key = f"hr_notes_{emp_id}"
    emp["hr_notes"] = st.session_state.get(key, "")
    save_employee(emp)
    st.session_state[f"hr_notes_saved_at_{emp_id}"] = datetime.now()


def hr_deep_dive():
    st.header("👥 Employee Deep Dive")
    employees = load_employees()
    names = [e["name"] for e in employees]
    idx = 0
    selected_name = st.selectbox("Select Employee to Review", names, index=idx, key="hr_deep_select")
    emp = next(e for e in employees if e["name"] == selected_name)
    scores = data_agent.get_performance_score(emp)
    rating, band = manager_agent.suggest_rating(scores)
    status = emp.get("review_status", "pending")
    status_color = DANGER if status == "pending" else SUCCESS
    st.markdown(
        f"<div class='card'><h3>{emp['name']}</h3>{emp['role']} | {emp['department']} | Manager: {emp['manager']}<br>"
        f"<span class='badge' style='background:{status_color};color:white'>{status}</span> "
        f"<span class='badge' style='background:#efefef;color:#2a2a2a'>Overall {scores['overall_score']:.1f}/10</span> "
        f"<span class='badge' style='background:#e8f7ee;color:#167c3a'>{rating:.1f}/5 - {band}</span></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.subheader("📊 Raw Performance Data")
        j = emp["jira_data"]
        g = emp["github_data"]
        cf = emp["confluence_data"]
        h = emp["hr_data"]
        st.markdown("**JIRA**")
        st.metric("Tickets Closed", j.get("tickets_closed", 0))
        st.metric("Sprint Velocity", j.get("sprint_velocity_avg", 0))
        st.metric("On-time Delivery %", j.get("on_time_delivery_percent", 0))
        st.metric("Bugs Reported Against", j.get("bugs_reported_against", 0))
        st.metric("Critical Issues Resolved", j.get("critical_issues_resolved", 0))
        st.markdown("**GITHUB**")
        st.metric("Total Commits", g.get("total_commits", 0))
        st.metric("PRs Merged", g.get("prs_merged", 0))
        st.metric("PRs Reviewed", g.get("prs_reviewed", 0))
        st.metric("Code Review Comments", g.get("code_review_comments", 0))
        st.markdown("**CONFLUENCE**")
        st.metric("Docs Created", cf.get("docs_created", 0))
        st.metric("Docs Updated", cf.get("docs_updated", 0))
        st.metric("Views by Others", cf.get("pages_viewed_by_others", 0))
        st.markdown("**HR**")
        st.metric("Goals Completed / Total", f"{h.get('goals_completed', 0)} / {h.get('goals_set', 0)}")
        st.metric("Attendance %", h.get("attendance_percentage", 0))
        st.metric("Last Rating", h.get("last_rating", 0))
        st.metric("Years Experience", h.get("years_experience", 0))
    with c2:
        st.subheader("📈 Performance Scores vs Team")
        dims = ["delivery_score", "quality_score", "collaboration_score", "documentation_score", "goal_score"]
        labels = ["Delivery", "Quality", "Collaboration", "Documentation", "Goals"]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[scores[d] for d in dims], theta=labels, fill="toself", name=emp["name"]))
        fig.add_trace(go.Scatterpolar(r=[TEAM_AVERAGES[d] for d in dims], theta=labels, fill="toself", name="Team Avg"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=430)
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        st.subheader("🔍 AI Analysis")
        bias = data_agent.detect_bias_risk(emp, scores)
        if bias["risk_level"] == "HIGH":
            st.error(bias["message"])
        elif bias["risk_level"] == "MEDIUM":
            st.warning(bias["message"])
        else:
            st.success(bias["message"])
        contrib = data_agent.detect_invisible_contributions(emp)
        st.markdown("**Invisible Contributions**")
        if contrib:
            st.markdown(" ".join([f"<span class='badge' style='background:#e8f7ee;color:#167c3a'>{c}</span>" for c in contrib]), unsafe_allow_html=True)
        else:
            st.info("No invisible contributions detected")
        if st.button("🤖 Generate AI Review Draft", key=f"hr_ai_review_{emp['employee_id']}"):
            if not ollama_ok():
                ai_error()
            else:
                with st.spinner("🤖 Llama is thinking..."):
                    st.session_state[f"hr_ai_review_text_{emp['employee_id']}"] = manager_agent.generate_draft_review(emp["employee_id"])
        rr = st.session_state.get(f"hr_ai_review_text_{emp['employee_id']}")
        if rr:
            st.markdown(f"<div class='exec-box'>{rr['review_text']}</div>", unsafe_allow_html=True)
            stars = "★" * int(round(rr["recommended_rating"])) + "☆" * (5 - int(round(rr["recommended_rating"])))
            st.write(f"**Recommended Rating:** {stars} ({rr['recommended_rating']:.1f}/5)")
            st.markdown(
                f"<span class='badge' style='background:#dce8ff;color:#12408a'>{rr['recommended_band']}</span>",
                unsafe_allow_html=True,
            )

    st.subheader("✍️ HR Notes")
    notes_key = f"hr_notes_{emp['employee_id']}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = emp.get("hr_notes", "")
    st.text_area("Add observations", key=notes_key, height=120, on_change=_autosave_hr_notes, args=(emp["employee_id"],))
    saved_at = st.session_state.get(f"hr_notes_saved_at_{emp['employee_id']}")
    if saved_at and (datetime.now() - saved_at).seconds < 3:
        st.caption("✅ Saved")
    if st.button("✅ Approve This Review", key=f"hr_approve_{emp['employee_id']}"):
        emp["review_status"] = "approved_by_hr"
        emp["hr_approved_timestamp"] = datetime.now().isoformat(timespec="seconds")
        emp["hr_approver_id"] = st.session_state["user_id"]
        top_dim = max(
            ["delivery_score", "quality_score", "collaboration_score", "documentation_score", "goal_score"],
            key=lambda x: scores[x],
        ).replace("_score", "").title()
        weak_dim = min(
            ["delivery_score", "quality_score", "collaboration_score", "documentation_score", "goal_score"],
            key=lambda x: scores[x],
        ).replace("_score", "").title()
        rating = float(emp.get("final_rating", manager_agent.suggest_rating(scores)[0]))
        band = emp.get("recommended_band", manager_agent.suggest_rating(scores)[1])
        top_metric = f"{emp['jira_data'].get('tickets_closed', 0)} tickets closed"
        if ollama_ok():
            with st.spinner("🤖 Llama is thinking..."):
                feedback = hr_agent._call_llama(
                    system_prompt=(
                        "You are an HR system generating a warm, encouraging feedback summary for an "
                        "employee after their performance review is approved. Be positive, specific, and "
                        "motivating. Max 100 words."
                    ),
                    user_prompt=(
                        f"Generate approval feedback for {emp['name']} who received {rating}/5 ({band}) "
                        f"for Q1 2026. Their top strength was {top_dim}. Key achievement: {top_metric}. "
                        f"Area to improve: {weak_dim}."
                    ),
                )
        else:
            feedback = f"Great work this quarter, {emp['name']}! Your effort in {top_dim} stood out."
        emp["approval_feedback"] = feedback
        save_employee(emp)
        st.success("Review Approved!")
        st.balloons()
        st.info(feedback)
        st.caption("Employee will see this in their My Feedback tab")
        st.rerun()


def hr_bias_center():
    st.header("🚨 Bias Risk Center")
    for emp in load_employees():
        scores = data_agent.get_performance_score(emp)
        bias = data_agent.detect_bias_risk(emp, scores)
        if emp.get("bias_dismissed"):
            continue
        if bias["risk_level"] in ("HIGH", "MEDIUM"):
            card = st.container(border=True)
            with card:
                st.write(f"**{emp['name']}** | {emp['role']} | Manager: {emp['manager']}")
                st.write(f"Data score: {scores['overall_score']:.1f}/10 vs Last rating: {emp['hr_data'].get('last_rating', 0)}")
                st.write(f"Risk: {bias['risk_level']}")
                c1, c2 = st.columns(2)
                if c1.button("Flag for Review", key=f"flag_{emp['employee_id']}"):
                    emp["bias_flagged"] = True
                    save_employee(emp)
                    st.success("Flagged.")
                if c2.button("Dismiss", key=f"dismiss_{emp['employee_id']}"):
                    emp["bias_dismissed"] = True
                    save_employee(emp)
                    st.info("Dismissed.")
                    st.rerun()


def hr_nudge_manager():
    st.header("📧 Nudge Manager")
    pending_by_manager = {}
    for emp in load_employees():
        if emp.get("review_status") != "completed" and emp.get("review_status") != "approved_by_hr":
            pending_by_manager[emp["manager"]] = pending_by_manager.get(emp["manager"], 0) + 1
    days_left = (datetime(2026, 4, 20) - datetime.now()).days
    for manager_name, count in pending_by_manager.items():
        with st.container(border=True):
            st.write(f"**{manager_name}**")
            st.write(f"Pending: {count} | Days until deadline: {max(days_left, 0)}")
            if st.button("Send Nudge", key=f"nudge_{manager_name}"):
                if not ollama_ok():
                    ai_error()
                else:
                    with st.spinner("🤖 Llama is thinking..."):
                        msg = hr_agent.generate_completion_nudge(manager_name, count)
                    st.session_state[f"nudge_msg_{manager_name}"] = msg
            msg = st.session_state.get(f"nudge_msg_{manager_name}")
            if msg:
                st.info(msg)
                if st.button("Confirm Send", key=f"confirm_nudge_{manager_name}"):
                    st.session_state[f"nudged_at_{manager_name}"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("Nudge sent.")
            sent_at = st.session_state.get(f"nudged_at_{manager_name}")
            if sent_at:
                st.caption(f"Nudged at: {sent_at}")


def hr_reports():
    st.header("📋 Reports")
    if st.button("Generate Executive Report"):
        if not ollama_ok():
            ai_error()
        else:
            with st.spinner("🤖 Llama is thinking..."):
                report = hr_agent.generate_hr_summary_report()
            st.session_state["exec_report"] = report
    report = st.session_state.get("exec_report")
    if report:
        st.markdown(f"<div class='exec-box'>{report}</div>", unsafe_allow_html=True)
        st.download_button("Download as text", data=report, file_name="executive_report_q1_2026.txt")
    timeline = pd.DataFrame(
        {
            "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "Completion %": [10, 35, 65, 100],
        }
    )
    st.plotly_chart(px.line(timeline, x="Week", y="Completion %", markers=True, range_y=[0, 100]), use_container_width=True)


def manager_team() -> list:
    manager_name = st.session_state["user_name"]
    return [e for e in load_employees() if e.get("manager") == manager_name]


def manager_overview():
    st.header("📊 My Team Overview")
    team = manager_team()
    if not team:
        st.info("No team members mapped to this manager.")
        return
    avg = sum(data_agent.get_performance_score(e)["overall_score"] for e in team) / len(team)
    completed = sum(1 for e in team if e.get("review_status") == "completed")
    st.metric("Team Average Score", f"{avg:.1f}/10")
    st.progress(completed / len(team))
    for e in team:
        s = data_agent.get_performance_score(e)
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        c1.write(f"**{e['name']}**")
        c2.write(f"{e['role']} | {s['overall_score']:.1f}/10")
        c3.write(e.get("review_status", "pending"))
        if c4.button("Start Review", key=f"start_{e['employee_id']}"):
            st.session_state["current_page"] = "✍️ Write Reviews"
            st.session_state["mgr_selected_emp"] = e["employee_id"]
            st.rerun()


def manager_write_reviews():
    st.header("✍️ Write Reviews")
    team = manager_team()
    if not team:
        st.info("No direct reports found.")
        return
    default = st.session_state.get("mgr_selected_emp", team[0]["employee_id"])
    ids = [e["employee_id"] for e in team]
    idx = ids.index(default) if default in ids else 0
    emp = team[st.selectbox("Select Employee", range(len(team)), format_func=lambda i: f"{team[i]['name']} ({team[i]['employee_id']})", index=idx)]
    if st.button("Generate Draft Review"):
        if not ollama_ok():
            ai_error()
        else:
            with st.spinner("🤖 Llama is thinking..."):
                st.session_state[f"mgr_draft_{emp['employee_id']}"] = manager_agent.generate_draft_review(emp["employee_id"])
    draft = st.session_state.get(f"mgr_draft_{emp['employee_id']}")
    if draft:
        text = st.text_area("Review Text", value=draft["review_text"], height=220, key=f"mgr_text_{emp['employee_id']}")
        rating = st.slider("Recommended Rating (stars)", 1, 5, int(round(draft["recommended_rating"])))
        band = st.selectbox("Band", ["Exceptional", "Exceeds Expectations", "Meets Expectations", "Below Expectations", "Needs Improvement"], index=2)
        if st.button("Submit Review", type="primary"):
            emp["review_text"] = text
            emp["final_rating"] = float(rating)
            emp["recommended_band"] = band
            emp["review_status"] = "completed"
            emp["reviewer_id"] = st.session_state["user_id"]
            emp["review_timestamp"] = datetime.now().isoformat(timespec="seconds")
            save_employee(emp)
            st.success(f"Great work on completing {emp['name']}'s review! Rating submitted: {rating}/5 — {band}")
            st.balloons()


def manager_nudges():
    st.header("📧 Send Nudges")
    for emp in manager_team():
        if emp.get("self_assessment", "").strip():
            continue
        with st.container(border=True):
            st.write(f"**{emp['name']}** has not submitted self assessment.")
            if st.button("Generate Nudge", key=f"mgr_nudge_{emp['employee_id']}"):
                if not ollama_ok():
                    ai_error()
                else:
                    with st.spinner("🤖 Llama is thinking..."):
                        msg = manager_agent.generate_nudge_message(emp["employee_id"], 5)
                    st.session_state[f"mgr_nudge_text_{emp['employee_id']}"] = msg
            msg = st.session_state.get(f"mgr_nudge_text_{emp['employee_id']}")
            if msg:
                st.info(msg)
                if st.button("Send", key=f"send_mgr_nudge_{emp['employee_id']}"):
                    st.success("Nudge sent.")


def manager_analytics():
    st.header("📈 Team Analytics")
    team = manager_team()
    if not team:
        return
    tdf = pd.DataFrame(
        [{"Name": e["name"], "Overall": data_agent.get_performance_score(e)["overall_score"]} for e in team]
    )
    st.plotly_chart(px.bar(tdf, x="Name", y="Overall", range_y=[0, 10]), use_container_width=True)
    dims = ["delivery_score", "quality_score", "collaboration_score", "documentation_score", "goal_score"]
    labels = ["Delivery", "Quality", "Collaboration", "Documentation", "Goals"]
    avg_scores = {d: sum(data_agent.get_performance_score(e)[d] for e in team) / len(team) for d in dims}
    fig = go.Figure(go.Scatterpolar(r=[avg_scores[d] for d in dims], theta=labels, fill="toself", name="Team Avg"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])))
    st.plotly_chart(fig, use_container_width=True)
    tavg = sum(tdf["Overall"]) / len(tdf)
    tdf["Status"] = tdf["Overall"].apply(lambda v: "Above Avg" if v >= tavg else "Below Avg")
    st.dataframe(tdf, use_container_width=True, hide_index=True)


def employee_record():
    return find_employee(st.session_state["user_id"])


def employee_dashboard():
    emp = employee_record()
    if not emp:
        st.error("Employee record not found.")
        return
    st.header("🏠 My Dashboard")
    s = data_agent.get_performance_score(emp)
    st.markdown(f"<div class='card'><b>{emp['name']}</b> | {emp['role']} | {emp['review_period']}</div>", unsafe_allow_html=True)
    st.metric("Overall Score", f"{s['overall_score']:.1f}/10")
    for k, label in [
        ("delivery_score", "Delivery"),
        ("quality_score", "Quality"),
        ("collaboration_score", "Collaboration"),
        ("documentation_score", "Documentation"),
        ("goal_score", "Goals"),
    ]:
        st.write(f"{label}: {s[k]:.1f}/10 | Team: {TEAM_AVERAGES[k]:.1f}")
        st.progress(s[k] / 10)
    status = emp.get("review_status", "pending")
    if status == "pending":
        st.warning("Your review is pending. Manager has not submitted yet.")
    elif status == "completed":
        st.info("✅ Your review is complete! See feedback below.")
    elif status == "approved_by_hr":
        st.success("✅ Your review is HR approved.")
        st.markdown(
            f"<div class='exec-box'>{emp.get('review_text', 'No review text')}<br><br>"
            f"Rating: {emp.get('final_rating')} / 5 | Band: {emp.get('recommended_band')}</div>",
            unsafe_allow_html=True,
        )


def employee_self_assessment():
    emp = employee_record()
    if not emp:
        return
    st.header("✍️ Self Assessment")
    s = data_agent.get_performance_score(emp)
    st.write(f"Context: Overall {s['overall_score']:.1f}/10 | Tickets {emp['jira_data'].get('tickets_closed', 0)} | Commits {emp['github_data'].get('total_commits', 0)}")
    if st.button("Generate Draft with AI"):
        if not ollama_ok():
            ai_error()
        else:
            with st.spinner("🤖 Llama is thinking..."):
                st.session_state[f"sa_{emp['employee_id']}"] = employee_agent.generate_self_assessment(emp["employee_id"])
    draft = st.session_state.get(f"sa_{emp['employee_id']}", emp.get("self_assessment", ""))
    text = st.text_area("Self Assessment", value=draft, height=260)
    st.caption(f"Character count: {len(text)}")
    if st.button("Submit Self Assessment"):
        emp["self_assessment"] = text
        save_employee(emp)
        st.success("🎉 Self assessment submitted successfully!")


def employee_progress():
    emp = employee_record()
    if not emp:
        return
    st.header("📊 My Progress")
    s = data_agent.get_performance_score(emp)["overall_score"]
    trend = pd.DataFrame(
        {
            "Quarter": ["Q3 2025", "Q4 2025", "Q1 2026"],
            "Score": [max(0, s - 1.0), max(0, s - 0.4), s],
        }
    )
    st.plotly_chart(px.line(trend, x="Quarter", y="Score", markers=True, range_y=[0, 10]), use_container_width=True)
    dims = ["delivery_score", "quality_score", "collaboration_score", "documentation_score", "goal_score"]
    labels = ["Delivery", "Quality", "Collaboration", "Documentation", "Goals"]
    ms = data_agent.get_performance_score(emp)
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[ms[d] for d in dims], theta=labels, fill="toself", name="Me"))
    fig.add_trace(go.Scatterpolar(r=[TEAM_AVERAGES[d] for d in dims], theta=labels, fill="toself", name="Team"))
    st.plotly_chart(fig, use_container_width=True)
    contrib = data_agent.detect_invisible_contributions(emp)
    st.write("Invisible contributions:", ", ".join(contrib) if contrib else "None")
    st.write("Goal Completion Tracker")
    goals_set = emp["hr_data"].get("goals_set", 0)
    goals_completed = emp["hr_data"].get("goals_completed", 0)
    for i in range(goals_set):
        st.checkbox(f"Goal {i + 1}", value=i < goals_completed, disabled=True)


def employee_feedback():
    emp = employee_record()
    if not emp:
        return
    st.header("💬 My Feedback")
    if emp.get("review_status") != "approved_by_hr":
        st.info("⏳ Your feedback is not ready yet. Check back after your manager completes your review.")
        return
    st.markdown(
        f"<div class='exec-box'>{emp.get('review_text', '')}<br><br>"
        f"Rating: {'★'*int(round(emp.get('final_rating', 0)))} ({emp.get('final_rating', 0)}/5) | "
        f"Band: {emp.get('recommended_band', 'N/A')}<br>"
        f"HR Approved: {emp.get('hr_approved_timestamp', 'N/A')}<br><br>"
        f"<b style='color:{SUCCESS}'>Strengths:</b> {data_agent.detect_invisible_contributions(emp)}<br>"
        f"<b style='color:{WARN}'>Areas to improve:</b> Documentation, consistency in goals<br><br>"
        f"{emp.get('approval_feedback', '')}</div>",
        unsafe_allow_html=True,
    )


def render_app():
    role = st.session_state["role"]
    page = st.session_state["current_page"]
    if role == "HR Admin":
        if page == "📊 Overview Dashboard":
            hr_overview()
        elif page == "👥 Employee Deep Dive":
            hr_deep_dive()
        elif page == "🚨 Bias Risk Center":
            hr_bias_center()
        elif page == "📧 Nudge Manager":
            hr_nudge_manager()
        elif page == "📋 Reports":
            hr_reports()
    elif role == "Manager":
        if page == "📊 My Team Overview":
            manager_overview()
        elif page == "✍️ Write Reviews":
            manager_write_reviews()
        elif page == "📧 Send Nudges":
            manager_nudges()
        elif page == "📈 Team Analytics":
            manager_analytics()
    else:
        if page == "🏠 My Dashboard":
            employee_dashboard()
        elif page == "✍️ Self Assessment":
            employee_self_assessment()
        elif page == "📊 My Progress":
            employee_progress()
        elif page == "💬 My Feedback":
            employee_feedback()


if not st.session_state.get("is_logged_in"):
    login_page()
else:
    sidebar_nav()
    render_app()
