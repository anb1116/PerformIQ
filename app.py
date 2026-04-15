import json
from datetime import datetime
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from agents.data_agent import ALL_EMPLOYEES, TEAM_AVERAGES, DataAggregatorAgent
from agents.employee_agent import EmployeeCoachAgent
from agents.hr_agent import HROrchestratorAgent
from agents.intelligence_agent import IntelligenceAgent, build_employee_dataset, run_analysis
from agents.manager_agent import ManagerAssistantAgent

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="PerformIQ", page_icon="⚡", layout="wide")

# ── GLOBAL CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── RESET ── */
.stApp { background: #F8FAFC !important; }
#MainMenu, footer, header { visibility: hidden; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }

/* ── GLOBAL READABILITY ── */
/* Keep dark text only in light content regions */
.piq-content, .piq-content p, .piq-content span, .piq-content li,
.piq-header, .piq-header p, .piq-header span, .piq-header li,
.piq-card, .piq-card p, .piq-card span, .piq-card li,
.metric-card, .metric-card p, .metric-card span, .metric-card li,
.review-box {
    color: #0F172A !important;
}

/* Ensure Streamlit markdown/headers stay readable on light surfaces */
.piq-content .stMarkdown,
.piq-content .stMarkdown p,
.piq-content .stMarkdown div,
.piq-content .stMarkdown span,
.piq-content .stMarkdown li,
.piq-content .stMarkdown strong,
.piq-content h1, .piq-content h2, .piq-content h3, .piq-content h4 {
    color: #0F172A !important;
}
.piq-content .stMarkdown small {
    color: #475569 !important;
}

/* Keep text readable in dark sections */
.login-topbar, .login-topbar p, .login-topbar span, .login-topbar li,
.login-card, .login-card p, .login-card span, .login-card li,
.hero-pill, .stat-pill {
    color: #E2E8F0 !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #0A0D14 !important;
    border-right: 1px solid #1A1F2E;
    min-width: 240px !important;
    max-width: 240px !important;
}
section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: #94A3B8 !important;
    text-align: left !important;
    padding: 10px 16px !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: all 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #1A1F2E !important;
    color: #F1F5F9 !important;
}

/* ── MAIN BUTTONS ── */
.stButton > button {
    background: #7C3AED !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.15s !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: #6D28D9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(124,58,237,0.3) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
}

/* BaseWeb select + options text */
div[data-baseweb="select"] * {
    color: #0F172A !important;
}
[data-testid="stSelectbox"] svg {
    fill: #475569 !important;
}

/* Streamlit widget labels */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stRadio label,
.stCheckbox label {
    color: #334155 !important;
}

/* Streamlit alerts/messages readable on light backgrounds */
[data-testid="stAlert"] {
    color: #0F172A !important;
}
[data-testid="stAlert"] * {
    color: inherit !important;
}

/* ── PROGRESS ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #7C3AED, #2563EB) !important;
    border-radius: 999px !important;
}

/* ── RADIO ── */
.stRadio > div { flex-direction: row !important; gap: 8px !important; }

/* ── LOGIN PAGE ── */
.login-bg {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: #0A0D14; z-index: -1;
}
.login-topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 56px;
    background: #0A0D14; border-bottom: 1px solid #1A1F2E;
    z-index: 1000; display: flex; align-items: center;
    justify-content: space-between; padding: 0 32px;
}
.hero-pill {
    display: inline-block; background: #1E1B4B; color: #A78BFA;
    border-radius: 999px; padding: 6px 14px;
    font-size: 12px; font-weight: 600; margin-bottom: 20px;
}
.stat-pill {
    display: inline-block; background: #131929; color: #94A3B8;
    border: 1px solid #2D3554; border-radius: 999px;
    padding: 7px 14px; font-size: 12px; font-weight: 700; margin: 0 4px;
}
.login-card {
    max-width: 440px; margin: 0 auto;
    background: #131929; border: 1px solid #2D3554;
    border-radius: 16px; padding: 32px 28px;
    box-shadow: 0 32px 64px rgba(0,0,0,0.5);
}
.user-found-card {
    background: #071A0F; border: 1px solid #059669;
    border-radius: 8px; padding: 12px 16px; margin-top: 8px;
}
.user-not-found-card {
    background: #1A0505; border: 1px solid #DC2626;
    border-radius: 8px; padding: 10px 14px; margin-top: 8px;
}

/* ── CONTENT AREA ── */
.piq-content { padding: 0 32px 40px 32px; }
.piq-header {
    padding: 24px 32px 20px 32px;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 28px;
    background: #FFFFFF;
}
.piq-title { font-size: 22px; font-weight: 700; color: #0F172A; margin: 0 0 2px 0; }
.piq-subtitle { font-size: 13px; color: #94A3B8; margin: 0; }

/* ── CARDS ── */
.piq-card {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.piq-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.piq-card-title { font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 2px; }
.piq-card-sub { font-size: 13px; color: #64748B; }

/* ── METRIC CARDS ── */
.metric-card {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 20px 16px;
    text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-value { font-size: 34px; font-weight: 800; line-height: 1; margin-bottom: 6px; }
.metric-label {
    font-size: 11px; color: #94A3B8; text-transform: uppercase;
    letter-spacing: 0.07em; font-weight: 600;
}
.metric-sub { font-size: 11px; color: #64748B; margin-top: 3px; }

/* ── BADGES ── */
.badge {
    display: inline-block; padding: 3px 10px;
    border-radius: 999px; font-size: 11px; font-weight: 700;
}
.badge-purple { background: #F3F0FF; color: #6D28D9; }
.badge-blue   { background: #EFF6FF; color: #1D4ED8; }
.badge-green  { background: #ECFDF5; color: #065F46; }
.badge-red    { background: #FEF2F2; color: #991B1B; }
.badge-amber  { background: #FFFBEB; color: #92400E; }
.badge-gray   { background: #F1F5F9; color: #475569; }

/* ── BIAS ALERTS ── */
.alert-high {
    background: #FEF2F2; border: 1px solid #FECACA;
    border-left: 4px solid #DC2626; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 12px;
    color: #7F1D1D !important;
}
.alert-medium {
    background: #FFFBEB; border: 1px solid #FDE68A;
    border-left: 4px solid #D97706; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 12px;
    color: #78350F !important;
}
.alert-low {
    background: #ECFDF5; border: 1px solid #A7F3D0;
    border-left: 4px solid #059669; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 12px;
    color: #065F46 !important;
}
.alert-high *, .alert-medium *, .alert-low * { color: inherit !important; }

/* ── REVIEW BOX ── */
.review-box {
    background: #FAFAFA; border: 1px solid #E2E8F0;
    border-radius: 10px; padding: 20px 24px;
    font-size: 14px; line-height: 1.8; color: #1E293B;
    white-space: pre-wrap;
}

/* ── SCORE DISPLAY ── */
.score-big {
    font-size: 56px; font-weight: 800;
    background: linear-gradient(135deg, #7C3AED, #2563EB);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1; margin-bottom: 4px;
}

/* ── SECTION DIVIDER ── */
.section-divider { height: 1px; background: #E2E8F0; margin: 24px 0; }

/* ── LIVE BADGE ── */
.live-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0;
    border-radius: 999px; padding: 3px 10px; font-size: 11px; font-weight: 700;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #059669; animation: pulse 2s infinite;
    display: inline-block;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* ── SUBMISSION SUCCESS ── */
.submit-success {
    background: #F0FDF4; border: 1px solid #BBF7D0;
    border-left: 4px solid #059669; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 16px;
}

/* ── STAT ROW ── */
.stat-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0; border-bottom: 1px solid #F1F5F9;
}
.stat-label { font-size: 13px; color: #64748B; font-weight: 500; }
.stat-value { font-size: 13px; color: #0F172A; font-weight: 700; }

/* ── INVISIBLE CONTRIB TAG ── */
.contrib-tag {
    display: inline-block; background: #ECFDF5; color: #065F46;
    border: 1px solid #A7F3D0; border-radius: 8px;
    padding: 6px 12px; font-size: 12px; font-weight: 600;
    margin: 4px 4px 4px 0;
}

/* ── PROFILE AVATAR ── */
.avatar {
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; color: white;
    flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent / "data"
NOTIFICATIONS_PATH = DATA_DIR / "_notifications.json"

USERS = {
    "HR001":  {"name":"Vikram Joshi",  "job":"HR Manager",          "dept":"HR",          "type":"HR"},
    "MGR001": {"name":"Amit Desai",    "job":"Tech Lead",            "dept":"Engineering", "type":"Manager"},
    "MGR002": {"name":"Rohan Gupta",   "job":"Operations Manager",   "dept":"Operations",  "type":"Manager"},
    "MGR003": {"name":"Arjun Nair",    "job":"Sales Manager",        "dept":"Sales",       "type":"Manager"},
    "EMP001": {"name":"Priya Sharma",  "job":"Senior Engineer",      "dept":"Engineering", "type":"Employee"},
    "EMP002": {"name":"Rahul Mehta",   "job":"Software Engineer",    "dept":"Engineering", "type":"Employee"},
    "EMP003": {"name":"Sneha Patil",   "job":"DevOps Engineer",      "dept":"Engineering", "type":"Employee"},
    "EMP004": {"name":"Ananya Singh",  "job":"Operations Analyst",   "dept":"Operations",  "type":"Employee"},
    "EMP005": {"name":"Neha Kulkarni", "job":"Product Manager",      "dept":"Operations",  "type":"Employee"},
    "EMP006": {"name":"Kavya Reddy",   "job":"Sales Executive",      "dept":"Sales",       "type":"Employee"},
}

ROLE_COLORS = {"HR": "#7C3AED", "Manager": "#2563EB", "Employee": "#059669"}
DEPT_COLORS = {
    "Engineering": "#7C3AED", "Operations": "#2563EB",
    "Sales": "#059669", "HR": "#D97706",
}


def _load_notifications() -> list:
    if not NOTIFICATIONS_PATH.exists():
        return []
    try:
        return json.loads(NOTIFICATIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_notifications(items: list) -> None:
    NOTIFICATIONS_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _user_id_by_name(name: str) -> str | None:
    for uid, meta in USERS.items():
        if meta.get("name", "").strip().lower() == (name or "").strip().lower():
            return uid
    return None


def push_notification(recipient_ids: list[str], message: str, kind: str = "info", actor_id: str = "") -> None:
    existing = _load_notifications()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for rid in recipient_ids:
        if not rid:
            continue
        existing.insert(
            0,
            {
                "recipient_id": rid,
                "actor_id": actor_id,
                "kind": kind,
                "message": message,
                "ts": ts,
            },
        )
    _save_notifications(existing[:800])


def notifications_for_user(user_id: str, limit: int = 8) -> list:
    return [n for n in _load_notifications() if n.get("recipient_id") == user_id][:limit]

# ── AGENTS ───────────────────────────────────────────────────
@st.cache_resource
def init_agents():
    return (
        DataAggregatorAgent(),
        ManagerAssistantAgent(),
        EmployeeCoachAgent(),
        HROrchestratorAgent(),
        IntelligenceAgent(),
    )

data_agent, manager_agent, employee_agent, hr_agent, intelligence_agent = init_agents()

# ── PERFORMANCE CACHE HELPERS ────────────────────────────────
@st.cache_data(ttl=30)
def cached_all_emps() -> list:
    return data_agent.get_all_employees()


@st.cache_data(ttl=30)
def cached_emp(employee_id: str) -> dict:
    return data_agent.get_employee_by_id(employee_id)


@st.cache_data(ttl=30)
def cached_scores_map() -> dict:
    emps = cached_all_emps()
    out = {}
    for e in emps:
        eid = e.get("employee_id")
        if eid:
            out[eid] = data_agent.get_performance_score(e)
    return out


# ── HELPERS ──────────────────────────────────────────────────
def rating_to_10(value: float) -> float:
    v = float(value or 0.0)
    if 0.0 < v <= 5.0:
        v *= 2.0
    return round(max(0.0, min(10.0, v)), 1)


def is_manager_review_submitted(status: str) -> bool:
    return (status or "").strip().lower() in ("completed", "approved_by_hr")


def normalized_bias_risk(emp: dict, scores: dict) -> dict:
    """UI-safe bias risk that always compares manager rating and score on /10 scale."""
    status = (emp.get("review_status") or "").strip().lower()
    has_submitted_review = is_manager_review_submitted(status)
    if not has_submitted_review:
        return {
            "risk_level": "NONE",
            "risk_label": "REVIEW NOT SUBMITTED",
            "message": "Bias comparison appears only after manager submits the review.",
            "show_bias": False,
        }

    base = data_agent.detect_bias_risk(emp, scores)
    source_rating = emp.get("final_rating", None)
    if source_rating is None:
        source_rating = emp.get("hr_data", {}).get("last_rating", 0)
    manager_rating_10 = rating_to_10(source_rating)
    data_score_10 = float(scores.get("overall_score", 0.0))
    gap = abs(round(data_score_10 - manager_rating_10, 2))
    if gap > 1.5:
        level, label = "HIGH", "HIGH BIAS RISK"
    elif gap > 0.8:
        level, label = "MEDIUM", "MEDIUM BIAS RISK"
    else:
        level, label = "LOW", "LOW BIAS RISK"
    direction = "above" if (manager_rating_10 - data_score_10) > 0 else "below"
    base["risk_level"] = level
    base["risk_label"] = label
    base["message"] = f"Manager rating is {gap:.1f} points {direction} data score."
    base["show_bias"] = True
    return base


def save_employee(emp: dict):
    target = DATA_DIR / f"{emp['employee_id']}.json"
    target.write_text(json.dumps(emp, indent=2), encoding="utf-8")
    ALL_EMPLOYEES[emp["employee_id"]] = emp
    # Clear caches so UI reflects latest write immediately.
    cached_all_emps.clear()
    cached_emp.clear()
    cached_scores_map.clear()
    get_cached_analytics_data.clear()


def initials(name: str) -> str:
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else name[:2].upper()


def avatar_html(name: str, color: str, size: int = 38) -> str:
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{color};display:flex;align-items:center;justify-content:center;'
        f'font-size:{size//3}px;font-weight:700;color:white;flex-shrink:0;">'
        f'{initials(name)}</div>'
    )


def metric_card(value: str, label: str, color: str, sub: str = ""):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="metric-card">'
        f'<div class="metric-value" style="color:{color}">{value}</div>'
        f'<div class="metric-label">{label}</div>{sub_html}</div>'
    )


def badge(text: str, kind: str = "gray") -> str:
    return f'<span class="badge badge-{kind}">{text}</span>'


def bias_alert_html(emp_name: str, risk: dict) -> str:
    level = risk["risk_level"]
    cls = "alert-high" if level == "HIGH" else "alert-medium" if level == "MEDIUM" else "alert-low"
    icon = "🚨" if level == "HIGH" else "⚠️" if level == "MEDIUM" else "✅"
    badge_color = "red" if level == "HIGH" else "amber" if level == "MEDIUM" else "green"
    return (
        f'<div class="{cls}">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-weight:700;color:#0F172A;font-size:14px;">{icon} {emp_name}</span>'
        f'{badge(risk["risk_label"], badge_color)}</div>'
        f'<div style="color:#64748B;font-size:13px;">{escape(risk["message"])}</div>'
        f'</div>'
    )


def section_header(title: str, subtitle: str = ""):
    sub = f'<div style="font-size:12px;color:#94A3B8;margin-top:2px;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:16px;">'
        f'<div style="font-size:16px;font-weight:700;color:#0F172A;">{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str):
    st.markdown(
        f'<div class="piq-header">'
        f'<div class="piq-title">{title}</div>'
        f'<div class="piq-subtitle">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_ai_narrative(result: dict) -> str:
    """Convert structured analytics output into readable narrative."""
    if not result:
        return "No analytics result available."
    if result.get("error"):
        return f"Analysis error: {result['error']}"

    title = result.get("title", "Analytics Result")
    insights = result.get("insights", []) or []
    recs = result.get("recommendations", []) or []

    # Strong deterministic formatter so we never show raw dict blocks.
    def _clean_row(row: dict) -> str:
        if not isinstance(row, dict):
            return str(row)
        if "statement" in row and row["statement"]:
            return str(row["statement"])
        if "employee" in row and "gap" in row:
            return f"{row.get('employee')} ({row.get('employee_id','')}) has rating gap {row.get('gap')}."
        if "employee" in row and "risk" in row:
            return f"{row.get('employee')} ({row.get('employee_id','')}) is {row.get('risk')} risk under {row.get('manager')}."
        if "manager" in row and "deviation_percent" in row:
            return f"{row.get('manager')} shows {row.get('deviation_percent')}% deviation ({row.get('severity','Low')} severity)."
        if "fairness_improvement_percent" in row:
            return f"Calibration improves fairness by {row.get('fairness_improvement_percent')}%."
        if "snapshot" in row and isinstance(row["snapshot"], dict):
            s = row["snapshot"]
            return (
                f"Team snapshot: {s.get('total_employees',0)} employees, "
                f"{s.get('completed_reviews',0)} completed, {s.get('pending_reviews',0)} pending, "
                f"avg score {s.get('avg_score',0)}."
            )
        return ", ".join([f"{k}: {v}" for k, v in list(row.items())[:4]])

    deterministic_lines = [f"{title}"]
    for row in insights[:3]:
        deterministic_lines.append(f"- {_clean_row(row)}")
    for rec in recs[:2]:
        deterministic_lines.append(f"- Next: {rec}")
    deterministic_text = "\n".join(deterministic_lines)

    # Fast deterministic rendering (no blocking model call in this UI path).
    return deterministic_text


def _analysis_points(title: str, insights: list) -> list[str]:
    pts: list[str] = []
    if title == "Weekly Digest" and insights:
        row = insights[0] if isinstance(insights[0], dict) else {}
        snap = row.get("snapshot", {}) if isinstance(row, dict) else {}
        if snap:
            pts.append(
                f"Org status: {snap.get('total_employees',0)} employees, "
                f"{snap.get('completed_reviews',0)} completed reviews, "
                f"{snap.get('pending_reviews',0)} pending, avg score {snap.get('avg_score',0)}/10."
            )
        for b in row.get("top_bias_cases", [])[:3]:
            pts.append(f"Bias hotspot: {b.get('employee','Unknown')} ({b.get('employee_id','')}) under {b.get('manager','Unknown')} with gap {b.get('rating_gap',0)}.")
        for u in row.get("top_underrated_cases", [])[:2]:
            pts.append(f"Under-rated: {u.get('employee','Unknown')} has score {u.get('data_score',0)}/10 vs manager {u.get('manager_rating',0)}/10.")
        return pts

    if title == "Bias Hotspots":
        for r in insights[:6]:
            if isinstance(r, dict):
                pts.append(f"{r.get('employee','Unknown')} ({r.get('employee_id','')}) is {r.get('risk','N/A')} risk under {r.get('manager','Unknown')} with rating gap {r.get('rating_gap',0)}.")
        return pts

    if title == "Review Priority Queue":
        for r in insights[:6]:
            if isinstance(r, dict):
                pts.append(f"Priority {r.get('employee','Unknown')} ({r.get('employee_id','')}) · urgency {r.get('urgency_score',0)} · {r.get('risk','N/A')} risk · manager {r.get('manager','Unknown')}.")
        return pts

    if title == "Rebalance Recommendations":
        for r in insights[:4]:
            if isinstance(r, dict) and "manager_load" in r:
                ml = r.get("manager_load", {})
                for mgr, cnt in ml.items():
                    pts.append(f"Manager load: {mgr} has {cnt} pending reviews.")
            else:
                pts.append(str(r))
        return pts

    if title == "Manager Risk Scorecard":
        for r in insights[:6]:
            if isinstance(r, dict):
                pts.append(
                    f"{r.get('manager','Unknown')} · team size {r.get('team_size',0)} · "
                    f"HIGH {r.get('high_bias_count',0)} · MEDIUM {r.get('medium_bias_count',0)} · "
                    f"risk score {r.get('risk_score',0)}."
                )
        return pts

    for item in insights[:6]:
        if isinstance(item, dict):
            short = ", ".join([f"{k}: {v}" for k, v in list(item.items())[:4]])
            pts.append(short)
        else:
            pts.append(str(item))
    return pts


def render_structured_analysis(result: dict):
    """Professional analyst-style output, never raw dict dumps."""
    if not result:
        return
    if result.get("error"):
        st.error(result["error"])
        return

    title = result.get("title", "Analysis")
    insights = result.get("insights", []) or []
    recs = result.get("recommendations", []) or []

    st.markdown(
        f"<div style='font-size:20px;font-weight:800;color:#0F172A;margin:4px 0 10px;'>{escape(title)}</div>",
        unsafe_allow_html=True,
    )

    # Weekly Digest: render nested blocks as explicit tables.
    if title == "Weekly Digest" and insights and isinstance(insights[0], dict):
        digest = insights[0]
        snapshot = digest.get("snapshot", {}) or {}
        if snapshot:
            snap_rows = "".join(
                f"<tr><td style='padding:8px 10px;color:#334155;'>{escape(str(k).replace('_',' ').title())}</td>"
                f"<td style='padding:8px 10px;color:#334155;'>{escape(str(v))}</td></tr>"
                for k, v in snapshot.items()
            )
            st.markdown("<div style='font-size:14px;font-weight:700;color:#0F172A;margin-top:8px;'>Snapshot</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="piq-card">
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                  <thead><tr style="border-bottom:1px solid #E2E8F0;">
                    <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>Metric</th>
                    <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>Value</th>
                  </tr></thead>
                  <tbody>{snap_rows}</tbody>
                </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for section_key, section_label in [
            ("top_bias_cases", "Top Bias Cases"),
            ("top_underrated_cases", "Top Underrated Cases"),
        ]:
            rows = digest.get(section_key, []) or []
            if not rows:
                continue
            cols = list(rows[0].keys())[:6] if isinstance(rows[0], dict) else ["Finding"]
            head = "".join(
                f"<th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>{escape(str(c).replace('_',' '))}</th>"
                for c in cols
            )
            body = ""
            for r in rows[:10]:
                if isinstance(r, dict):
                    body += "<tr>" + "".join(
                        f"<td style='padding:8px 10px;color:#334155;'>{escape(str(r.get(c,'')))}</td>"
                        for c in cols
                    ) + "</tr>"
                else:
                    body += f"<tr><td style='padding:8px 10px;color:#334155;'>{escape(str(r))}</td></tr>"
            st.markdown(f"<div style='font-size:14px;font-weight:700;color:#0F172A;margin-top:10px;'>{section_label}</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="piq-card">
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                  <thead><tr style="border-bottom:1px solid #E2E8F0;">{head}</tr></thead>
                  <tbody>{body}</tbody>
                </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Rebalance: render manager load map as manager/load table.
    elif title == "Rebalance Recommendations" and insights and isinstance(insights[0], dict) and isinstance(insights[0].get("manager_load"), dict):
        load = insights[0].get("manager_load", {}) or {}
        st.markdown("<div style='font-size:14px;font-weight:700;color:#0F172A;margin-top:8px;'>Manager Load</div>", unsafe_allow_html=True)
        load_rows = "".join(
            f"<tr><td style='padding:8px 10px;color:#334155;'>{escape(str(mgr))}</td>"
            f"<td style='padding:8px 10px;color:#334155;'>{escape(str(cnt))}</td></tr>"
            for mgr, cnt in sorted(load.items(), key=lambda x: x[1], reverse=True)
        )
        st.markdown(
            f"""
            <div class="piq-card">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead><tr style="border-bottom:1px solid #E2E8F0;">
                <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>Manager</th>
                <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>Pending Reviews</th>
              </tr></thead>
              <tbody>{load_rows}</tbody>
            </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Table-wise rendering for professional readability.
    elif insights:
        st.markdown("<div style='font-size:14px;font-weight:700;color:#0F172A;margin-top:8px;'>Key Findings</div>", unsafe_allow_html=True)
        if isinstance(insights[0], dict):
            keys = list(insights[0].keys())[:6]
            header = "".join(
                f"<th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>{escape(str(k).replace('_',' '))}</th>"
                for k in keys
            )
            body_rows = ""
            for row in insights[:10]:
                body_rows += "<tr>" + "".join(
                    f"<td style='padding:8px 10px;color:#334155;'>{escape(str(row.get(k,'')))}</td>"
                    for k in keys
                ) + "</tr>"
            st.markdown(
                f"""
                <div class="piq-card">
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                  <thead><tr style="border-bottom:1px solid #E2E8F0;">{header}</tr></thead>
                  <tbody>{body_rows}</tbody>
                </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            rows = "".join(
                f"<tr><td style='padding:8px 10px;color:#334155;'>{escape(str(p))}</td></tr>"
                for p in insights[:10]
            )
            st.markdown(
                f"""
                <div class="piq-card">
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                  <thead>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                      <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>Finding</th>
                    </tr>
                  </thead>
                  <tbody>{rows}</tbody>
                </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if recs:
        st.markdown("<div style='font-size:14px;font-weight:700;color:#0F172A;margin-top:10px;'>Recommended Actions</div>", unsafe_allow_html=True)
        action_rows = "".join(
            f"<tr><td style='padding:8px 10px;color:#334155;'>{idx}</td><td style='padding:8px 10px;color:#334155;'>{escape(str(r))}</td></tr>"
            for idx, r in enumerate(recs[:6], start=1)
        )
        st.markdown(
            f"""
            <div class="piq-card">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead>
                <tr style="border-bottom:1px solid #E2E8F0;">
                  <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>#</th>
                  <th style='padding:8px 10px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;'>Action</th>
                </tr>
              </thead>
              <tbody>{action_rows}</tbody>
            </table>
            </div>
            """,
            unsafe_allow_html=True,
        )


@st.cache_data(ttl=45)
def get_cached_analytics_data() -> dict:
    return build_employee_dataset()


def plotly_cfg() -> dict:
    return dict(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(family="Inter", color="#0F172A", size=13),
        margin=dict(l=16, r=16, t=40, b=24),
    )


# ── CHARTS ───────────────────────────────────────────────────
def radar_chart(my_scores: list, team_avg: list, labels: list, title: str = ""):
    cats = labels + [labels[0]]
    mine = my_scores + [my_scores[0]]
    team = team_avg + [team_avg[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=mine, theta=cats, fill="toself", name="You",
        line=dict(color="#7C3AED", width=2),
        fillcolor="rgba(124,58,237,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=team, theta=cats, fill="toself", name="Team Avg",
        line=dict(color="#94A3B8", width=1.5, dash="dot"),
        fillcolor="rgba(148,163,184,0.08)",
    ))
    fig.update_layout(
        **plotly_cfg(),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#E2E8F0",
                            tickfont=dict(size=10, color="#0F172A"), tickcolor="#94A3B8"),
            angularaxis=dict(gridcolor="#E2E8F0", tickfont=dict(size=11, color="#0F172A")),
            bgcolor="#FFFFFF",
        ),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
            font=dict(size=12, color="#0F172A"),
        ),
        title=dict(text=title, font=dict(size=14, color="#0F172A")),
        height=320,
    )
    return fig


def bar_chart_dept(labels: list, values: list, title: str):
    colors = [DEPT_COLORS.get(l, "#7C3AED") for l in labels]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors,
        text=[f"{v}/10" for v in values],
        textposition="outside", textfont=dict(size=12, color="#0F172A"),
    ))
    fig.update_layout(
        **plotly_cfg(),
        title=dict(text=title, font=dict(size=14, color="#0F172A")),
        xaxis=dict(gridcolor="#F1F5F9", tickfont=dict(size=12, color="#0F172A")),
        yaxis=dict(range=[0, 11], gridcolor="#F1F5F9", tickfont=dict(size=11, color="#0F172A")),
        height=280, showlegend=False,
    )
    return fig


def donut_chart(completed: int, total: int):
    pending = total - completed
    pct = int(completed / total * 100) if total else 0
    fig = go.Figure(go.Pie(
        labels=["Completed", "Pending"],
        values=[max(completed, 0), max(pending, 0)],
        hole=0.68,
        marker_colors=["#7C3AED", "#94A3B8"],
        textinfo="none",
    ))
    fig.update_layout(
        **plotly_cfg(),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=12, color="#0F172A"),
        ),
        height=260,
        annotations=[dict(
            text=f"<b>{pct}%</b>", x=0.5, y=0.5,
            font=dict(size=28, color="#7C3AED", family="Inter"),
            showarrow=False,
        )],
    )
    return fig


def team_bar_chart(names: list, scores: list):
    colors = ["#7C3AED" if s >= 7 else "#D97706" if s >= 5 else "#DC2626" for s in scores]
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker_color=colors,
        text=[f"{s}/10" for s in scores],
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig.update_layout(
        **plotly_cfg(),
        title=dict(text="Team Performance Overview", font=dict(size=14, color="#0F172A")),
        xaxis=dict(range=[0, 11.5], gridcolor="#F1F5F9", tickfont=dict(size=12, color="#0F172A")),
        yaxis=dict(gridcolor="#F1F5F9", tickfont=dict(size=12, color="#0F172A")),
        height=max(200, len(names) * 52),
        showlegend=False,
    )
    return fig


def score_trend_chart(name: str):
    quarters = ["Q3 2025", "Q4 2025", "Q1 2026"]
    import random; random.seed(hash(name) % 100)
    scores = [round(random.uniform(5.5, 8.5), 1) for _ in range(2)]
    emp = data_agent.get_employee_by_id(st.session_state["user_id"])
    current = data_agent.get_performance_score(emp)["overall_score"] if emp else 7.0
    scores.append(current)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=quarters, y=scores, mode="lines+markers+text",
        line=dict(color="#7C3AED", width=3),
        marker=dict(size=10, color="#7C3AED", line=dict(width=2, color="white")),
        text=[f"{s}" for s in scores], textposition="top center",
        textfont=dict(size=12, color="#7C3AED"),
        fill="tozeroy", fillcolor="rgba(124,58,237,0.07)",
    ))
    fig.update_layout(
        **plotly_cfg(),
        title=dict(text="Performance Trend", font=dict(size=14, color="#0F172A")),
        xaxis=dict(gridcolor="#F1F5F9", tickfont=dict(size=12, color="#0F172A")),
        yaxis=dict(range=[0, 11], gridcolor="#F1F5F9", tickfont=dict(size=12, color="#0F172A")),
        height=240,
    )
    return fig


# ── LOGIN PAGE ───────────────────────────────────────────────
def login_page():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background: #0A0D14 !important; }
    .stTextInput label { color: #94A3B8 !important; font-size: 12px !important;
                         font-weight: 600 !important; text-transform: uppercase !important;
                         letter-spacing: 0.06em !important; }
    .stTextInput input {
        background: #0D1117 !important; color: #F9FAFB !important;
        border: 1px solid #2D3554 !important; border-radius: 8px !important;
        font-size: 14px !important;
    }
    .stTextInput input:focus { border-color: #7C3AED !important; }
    .stCheckbox label { color: #94A3B8 !important; }
    </style>
    """, unsafe_allow_html=True)

    if "login_id" not in st.session_state:
        st.session_state["login_id"] = ""

    # Top bar
    st.markdown("""
    <div class="login-topbar">
      <div style="font-weight:800;font-size:18px;color:#F9FAFB;letter-spacing:-0.5px;">⚡ PerformIQ</div>
      <div style="font-size:12px;color:#94A3B8;">Agentic AI · Gemini 1.5 Pro · MIT-WPU 2026</div>
    </div>
    <div style="height:56px;"></div>
    """, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div style="text-align:center;padding:60px 24px 40px;">
      <div class="hero-pill">🤖 4 Autonomous Agents · Real-Time AI</div>
      <div style="font-size:48px;font-weight:800;color:#F9FAFB;line-height:1.15;
                  margin:16px 0 14px;letter-spacing:-1.5px;">
        Performance Reviews,<br>
        <span style="background:linear-gradient(135deg,#A78BFA,#60A5FA);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          Reimagined by AI.
        </span>
      </div>
      <p style="color:#94A3B8;font-size:15px;max-width:540px;margin:0 auto 20px;line-height:1.6;">
        Multi-agent system that turns Jira, GitHub and Confluence signals<br>into evidence-based performance reviews.
      </p>
      <div>
        <span class="stat-pill">🎯 92% Completion Rate</span>
        <span class="stat-pill">⚡ 3× Faster Reviews</span>
        <span class="stat-pill">🛡️ Bias Auto-Detected</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Login card
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:20px;">
      <div style="font-size:18px;font-weight:700;color:#F9FAFB;margin-bottom:4px;">Sign in to PerformIQ</div>
      <div style="font-size:13px;color:#94A3B8;">Use your work ID to continue</div>
    </div>
    """, unsafe_allow_html=True)

    uid_input = st.text_input("Work ID", placeholder="e.g. HR001, MGR001, EMP001",
                               key="login_id_raw", label_visibility="visible")
    uid = uid_input.strip().upper() if uid_input else ""
    user_record = USERS.get(uid)

    if user_record:
        role_color = ROLE_COLORS[user_record["type"]]
        st.markdown(f"""
        <div class="user-found-card">
          <div style="display:flex;align-items:center;gap:10px;">
            {avatar_html(user_record['name'], role_color, 36)}
            <div>
              <div style="color:#10B981;font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.05em;">✓ User Found</div>
              <div style="color:#F9FAFB;font-weight:600;font-size:14px;">{user_record['name']}</div>
              <div style="color:#94A3B8;font-size:12px;">{user_record['job']} · {user_record['dept']}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    elif len(uid) > 2:
        st.markdown("""
        <div class="user-not-found-card">
          <div style="color:#EF4444;font-weight:700;font-size:13px;">❌ Invalid ID</div>
          <div style="color:#94A3B8;font-size:12px;margin-top:2px;">Try HR001, MGR001, or EMP001–EMP006</div>
        </div>
        """, unsafe_allow_html=True)

    password = st.text_input("Password", type="password",
                              placeholder="Enter any password", key="login_pw")
    st.markdown('<div style="color:#94A3B8;font-size:11px;margin-top:2px;">Any password works for this demo</div>',
                unsafe_allow_html=True)

    btn_color = ROLE_COLORS.get(user_record["type"], "#7C3AED") if user_record else "#7C3AED"
    st.markdown(f"""
    <style>
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button {{
        background: {btn_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    if st.button("Sign in →", use_container_width=True, type="primary"):
        if not uid or not password.strip() or not user_record:
            st.error("❌ Invalid ID or empty password. Check your credentials.")
        else:
            st.session_state.update({
                "is_logged_in": True,
                "user_id": uid,
                "user_name": user_record["name"],
                "user_role": user_record["type"],
                "user_job": user_record["job"],
                "user_jobtitle": user_record["job"],
                "user_dept": user_record["dept"],
                "page": "Dashboard",
            })
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-top:20px;">
      <div style="color:#94A3B8;font-size:12px;">Demo credentials: HR001 · MGR001–003 · EMP001–006</div>
      <div style="color:#CBD5E1;font-size:11px;margin-top:4px;">Any password accepted</div>
    </div>
    """, unsafe_allow_html=True)


# ── SIDEBAR ──────────────────────────────────────────────────
def sidebar():
    role = st.session_state["user_role"]
    name = st.session_state["user_name"]
    job  = st.session_state["user_jobtitle"]
    dept = st.session_state["user_dept"]
    color = ROLE_COLORS[role]

    nav_map = {
        "HR":       ["Dashboard", "Reports"],
        "Manager":  ["Dashboard", "Write Reviews"],
        "Employee": ["Dashboard", "Self Assessment", "Feedback"],
    }
    pages = nav_map[role]

    nav_icons = {
        "Dashboard": "📊", "Reports": "📋",
        "Write Reviews": "✍️", "Self Assessment": "✍️", "Feedback": "💬",
    }

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:20px 16px 12px;">
          <div style="font-weight:800;font-size:18px;color:#F9FAFB;
                      letter-spacing:-0.5px;margin-bottom:12px;">⚡ PerformIQ</div>
          <div style="height:1px;background:linear-gradient(90deg,#7C3AED,transparent);
                      margin-bottom:16px;"></div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            {avatar_html(name, color, 36)}
            <div>
              <div style="font-weight:700;font-size:13px;color:#F1F5F9;">{name}</div>
              <div style="font-size:11px;color:#94A3B8;">{job}</div>
            </div>
          </div>
          <div style="margin-top:6px;">
            <span style="background:{color}22;color:{color};border:1px solid {color}44;
              border-radius:999px;padding:3px 10px;font-size:11px;font-weight:700;">
              {role}
            </span>
            <span style="background:#1A1F2E;color:#CBD5E1;border-radius:999px;
              padding:3px 10px;font-size:11px;margin-left:4px;">{dept}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height:1px;background:#1A1F2E;margin:0 16px 8px;"></div>',
                    unsafe_allow_html=True)

        current_page = st.session_state.get("page", "Dashboard")
        for p in pages:
            icon = nav_icons.get(p, "•")
            is_active = current_page == p
            active_style = (f"background:{color}22 !important;color:{color} !important;"
                            f"border-left:3px solid {color};") if is_active else ""
            st.markdown(f"""
            <style>
            div[data-testid="stButton"] > button[aria-label="nav_{p}"] {{
                {active_style}
            }}
            </style>
            """, unsafe_allow_html=True)
            if st.button(f"{icon}  {p}", use_container_width=True, key=f"nav_{p}"):
                st.session_state["page"] = p
                st.rerun()

        user_notifications = notifications_for_user(st.session_state.get("user_id", ""), limit=6)
        st.markdown('<div style="height:1px;background:#1A1F2E;margin:8px 16px 8px;"></div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="padding:0 16px 6px;font-size:11px;color:#94A3B8;text-transform:uppercase;letter-spacing:.06em;">Notifications</div>',
                    unsafe_allow_html=True)
        if user_notifications:
            for note in user_notifications:
                st.markdown(
                    f"<div style='margin:0 10px 8px;padding:8px 10px;border:1px solid #2D3554;border-radius:8px;background:#101726;'>"
                    f"<div style='font-size:10px;color:#94A3B8;'>{escape(note.get('ts',''))}</div>"
                    f"<div style='font-size:12px;color:#E2E8F0;margin-top:2px;'>{escape(note.get('message',''))}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div style='margin:0 10px 8px;padding:8px 10px;border:1px dashed #2D3554;border-radius:8px;color:#94A3B8;font-size:12px;'>No notifications yet.</div>",
                unsafe_allow_html=True,
            )

        st.markdown('<div style="height:1px;background:#1A1F2E;margin:8px 16px 8px;"></div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="padding:0 16px 4px;font-size:11px;color:#94A3B8;">Powered by Gemini 1.5 Pro</div>',
                    unsafe_allow_html=True)
        if st.button("← Logout", use_container_width=True, key="logout_btn"):
            st.session_state.clear()
            st.rerun()


# ── HELPER: TEAM MEMBERS ─────────────────────────────────────
def manager_team_members(manager_id: str) -> list:
    return [
        emp for eid in data_agent.get_team_members(manager_id)
        if (emp := cached_emp(eid))
    ]


# ── HR: DASHBOARD ────────────────────────────────────────────
def hr_dashboard():
    page_header("HR Command Center", "Q1 2026 · TechNova Pvt Ltd · Review Cycle")
    dashboard = hr_agent.get_cycle_dashboard()
    all_emps  = cached_all_emps()
    total     = len(all_emps)
    completed = sum(1 for e in all_emps if is_manager_review_submitted(e.get("review_status", "")))
    pending   = total - completed
    # Use the same "submitted-review bias" logic as the alerts section below.
    bias_flags = [
        e
        for e in all_emps
        if (lambda r: r.get("show_bias") and r.get("risk_level") in ("HIGH", "MEDIUM"))(
            normalized_bias_risk(e, data_agent.get_performance_score(e))
        )
    ]
    avg_score = round(
        (sum(data_agent.get_performance_score(e).get("overall_score", 0.0) for e in all_emps) / total),
        2,
    ) if total else 0.0

    # ── Metrics row ──
    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl, clr, sub in [
        (c1, f"{int(completed/total*100) if total else 0}%", "Completion Rate", "#7C3AED", f"{completed}/{total} reviews done"),
        (c2, str(pending),   "Pending Reviews", "#2563EB", "Need attention"),
        (c3, str(len(bias_flags)), "Bias Flags", "#DC2626", "Require review"),
        (c4, f"{avg_score}", "Avg Team Score",  "#059669", "Out of 10"),
    ]:
        with col:
            st.markdown(metric_card(val, lbl, clr, sub), unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Charts row ──
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        dept_scores: dict[str, list] = {}
        for emp in all_emps:
            d = emp.get("department", "Other")
            s = data_agent.get_performance_score(emp)["overall_score"]
            dept_scores.setdefault(d, []).append(s)
        dept_avgs = {d: round(sum(v)/len(v), 2) for d, v in dept_scores.items()}
        fig = bar_chart_dept(list(dept_avgs.keys()), list(dept_avgs.values()),
                             "Department Performance Scores")
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        fig2 = donut_chart(completed, total)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Review pipeline tracker ──
    section_header("🧭 Review Pipeline Status", "Live status of manager submission and HR approval")
    rows = ""
    for e in all_emps:
        status = (e.get("review_status") or "pending").strip().lower()
        if status == "approved_by_hr":
            status_badge = badge("HR Approved", "green")
        elif status == "completed":
            status_badge = badge("Manager Submitted", "amber")
        else:
            status_badge = badge("Pending", "gray")

        manager_ts = escape(str(e.get("review_timestamp") or "-"))
        hr_ts = escape(str(e.get("hr_approved_timestamp") or "-"))
        rows += (
            f"<tr>"
            f"<td style='padding:8px 10px;color:#0F172A;'>{escape(e.get('name',''))}</td>"
            f"<td style='padding:8px 10px;color:#334155;'>{escape(e.get('manager_name') or e.get('manager') or 'N/A')}</td>"
            f"<td style='padding:8px 10px;'>{status_badge}</td>"
            f"<td style='padding:8px 10px;color:#334155;'>{manager_ts}</td>"
            f"<td style='padding:8px 10px;color:#334155;'>{hr_ts}</td>"
            f"</tr>"
        )
    st.markdown(
        f"""
        <div class="piq-card">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="border-bottom:1px solid #E2E8F0;">
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;">Employee</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;">Manager</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;">Status</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;">Manager Submitted At</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;">HR Approved At</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Bias alerts ──
    section_header("🚨 Bias Risk Alerts", "Employees where review may be unfair")
    has_flags = False
    for emp in all_emps:
        scores = data_agent.get_performance_score(emp)
        risk   = normalized_bias_risk(emp, scores)
        if risk.get("show_bias") and risk["risk_level"] in ("HIGH", "MEDIUM"):
            has_flags = True
            st.markdown(bias_alert_html(emp.get("name",""), risk), unsafe_allow_html=True)
    if not has_flags:
        st.markdown('<div class="alert-low">✅ No significant bias detected across all employees.</div>',
                    unsafe_allow_html=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Employee deep dive ──
    section_header("👥 Employee Deep Dive", "Select any employee to inspect full profile")
    all_ids = [e["employee_id"] for e in all_emps if e.get("employee_id")]
    emp_lookup = {e.get("employee_id"): e for e in all_emps if e.get("employee_id")}
    sel_status = st.session_state.get("hr_emp_select")
    if sel_status and sel_status in emp_lookup:
        curr = (emp_lookup[sel_status].get("review_status") or "pending").strip().lower()
        if curr == "approved_by_hr":
            st.markdown('<div class="submit-success"><div style="font-weight:700;color:#059669;">✅ Current Status: HR Approved</div></div>', unsafe_allow_html=True)
        elif curr == "completed":
            st.markdown('<div class="alert-medium">🕒 Current Status: Manager Submitted (Awaiting HR action)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-low">ℹ️ Current Status: Pending manager submission</div>', unsafe_allow_html=True)
    sel = st.selectbox("Select Employee", all_ids,
                       format_func=lambda eid: f"{eid} · {emp_lookup.get(eid, {}).get('name','')}",
                       key="hr_emp_select")
    if sel:
        _render_employee_profile(sel, editable=True, show_generate=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── HR: REPORTS ──────────────────────────────────────────────
def hr_reports():
    page_header("Reports", "AI-generated executive summaries and cycle analytics")
    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)
    if "exec_report_editing" not in st.session_state:
        st.session_state["exec_report_editing"] = False

    all_emps = cached_all_emps()
    total    = len(all_emps)
    completed = sum(1 for e in all_emps if is_manager_review_submitted(e.get("review_status", "")))

    # ── Team score comparison ──
    section_header("📊 Full Team Performance", "All employees ranked by overall score")
    names  = [e.get("name","") for e in all_emps]
    scores = [data_agent.get_performance_score(e)["overall_score"] for e in all_emps]
    pairs  = sorted(zip(scores, names), reverse=True)
    fig = team_bar_chart([p[1] for p in pairs], [p[0] for p in pairs])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── AI Executive Report ──
    section_header("🤖 AI Executive Report", "Generated by Gemini 1.5 Pro")
    if st.button("Generate Executive Report", key="gen_exec_report"):
        with st.spinner("✨ Gemini is generating the report..."):
            try:
                report = hr_agent.generate_hr_summary_report()
                st.session_state["exec_report"] = report
                st.session_state["exec_report_editing"] = False
            except Exception as e:
                st.session_state["exec_report"] = f"Error generating report: {e}"
                st.session_state["exec_report_editing"] = False

    if st.session_state.get("exec_report"):
        c_rep_a, c_rep_b = st.columns([1, 1])
        with c_rep_a:
            if st.button("✏️ Modify Report", key="edit_exec_report_top"):
                st.session_state["exec_report_editing"] = True
                st.rerun()
        with c_rep_b:
            if st.session_state.get("exec_report_editing", False):
                if st.button("↩ Cancel Edit", key="cancel_exec_report_edit_top"):
                    st.session_state["exec_report_editing"] = False
                    st.rerun()

        if st.session_state.get("exec_report_editing", False):
            edited_report = st.text_area(
                "Edit Executive Report",
                value=st.session_state["exec_report"],
                height=260,
                key="exec_report_editor",
            )
            c_save, c_cancel = st.columns([1, 1])
            with c_save:
                if st.button("✅ Save Report Changes", type="primary", key="save_exec_report"):
                    if not edited_report.strip():
                        st.warning("Report cannot be empty.")
                    else:
                        st.session_state["exec_report"] = edited_report.strip()
                        st.session_state["exec_report_editing"] = False
                        st.success("Executive report updated.")
                        st.rerun()
            with c_cancel:
                if st.button("↩ Cancel", key="cancel_exec_report_edit"):
                    st.session_state["exec_report_editing"] = False
                    st.rerun()
        else:
            st.markdown(f'<div class="review-box">{escape(st.session_state["exec_report"])}</div>',
                        unsafe_allow_html=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── ADVANCED HR ANALYTICS (STANDARDIZED PIPELINE) ──
    section_header("🧠 Advanced HR Analytics", "Deterministic analytics pipeline with unified action runner")
    if "ai_result" not in st.session_state:
        st.session_state["ai_result"] = None

    st.markdown(
        "<div class='piq-card' style='padding:14px 16px;margin-bottom:12px;'>"
        "<div style='font-size:12px;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;'>Analysis Actions</div>"
        "<div style='font-size:13px;color:#334155;'>Choose a module to generate an analyst-ready insight.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Bias Hotspots", key="btn_bias_hotspots", use_container_width=True):
            with st.spinner("Analyzing..."):
                data = get_cached_analytics_data()
                result = run_analysis("bias_hotspots", data)
                st.session_state["ai_result"] = result
    with a2:
        if st.button("Weekly Digest", key="btn_weekly_digest", use_container_width=True):
            with st.spinner("Analyzing..."):
                data = get_cached_analytics_data()
                result = run_analysis("weekly_digest", data)
                st.session_state["ai_result"] = result
    with a3:
        if st.button("Manager Risk Scorecard", key="btn_mgr_risk", use_container_width=True):
            with st.spinner("Analyzing..."):
                data = get_cached_analytics_data()
                result = run_analysis("manager_risk_scorecard", data)
                st.session_state["ai_result"] = result

    b0, b1, b2, b3 = st.columns([0.5, 1, 1, 0.5])
    with b1:
        if st.button("Priority Queue", key="btn_priority_queue", use_container_width=True):
            with st.spinner("Analyzing..."):
                data = get_cached_analytics_data()
                result = run_analysis("priority_queue", data)
                st.session_state["ai_result"] = result
    with b2:
        if st.button("Rebalance Optimizer", key="btn_rebalance", use_container_width=True):
            with st.spinner("Analyzing..."):
                data = get_cached_analytics_data()
                result = run_analysis("rebalance_recommendations", data)
                st.session_state["ai_result"] = result

    if st.session_state["ai_result"]:
        render_structured_analysis(st.session_state["ai_result"])

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── X-FACTOR INTELLIGENCE LAYER ──
    section_header("🚀 X-Factor Intelligence Layer", "High-impact, deterministic insights for demo moments")
    if "xfactor_result" not in st.session_state:
        st.session_state["xfactor_result"] = None

    x1, x2, x3 = st.columns(3)
    with x1:
        if st.button("Manager Bias Explainer", key="x_bias_explainer", use_container_width=True):
            with st.spinner("Analyzing manager rating behavior..."):
                data = get_cached_analytics_data()
                result = run_analysis("manager_bias_explainer", data)
                st.session_state["xfactor_result"] = result
    with x2:
        if st.button("Weekly HR Action Plan", key="x_weekly_actions", use_container_width=True):
            with st.spinner("Generating top actions..."):
                data = get_cached_analytics_data()
                result = run_analysis("weekly_hr_action_plan", data)
                st.session_state["xfactor_result"] = result
    with x3:
        if st.button("Invisible Top Performer", key="x_hidden_top", use_container_width=True):
            with st.spinner("Detecting hidden top performers..."):
                data = get_cached_analytics_data()
                result = run_analysis("invisible_top_performer_detection", data)
                st.session_state["xfactor_result"] = result
    xres = st.session_state.get("xfactor_result")
    if xres:
        render_structured_analysis(xres)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Pending table ──
    section_header("📋 Pending Reviews", "Employees awaiting manager review")
    pending_emps = [e for e in all_emps if not is_manager_review_submitted(e.get("review_status", ""))]
    if pending_emps:
        if "manager_notifications" not in st.session_state:
            st.session_state["manager_notifications"] = []

        rows = ""
        for e in pending_emps:
            rows += (
                f"<tr><td>{e.get('name','')}</td>"
                f"<td>{e.get('role','')}</td>"
                f"<td>{e.get('department','')}</td>"
                f"<td>{e.get('manager_name','N/A')}</td>"
                f"<td>{badge('Pending','amber')}</td></tr>"
            )
        st.markdown(f"""
        <div class="piq-card">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="border-bottom:1px solid #E2E8F0;">
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em;">Employee</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-weight:600;font-size:11px;text-transform:uppercase;">Role</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-weight:600;font-size:11px;text-transform:uppercase;">Department</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-weight:600;font-size:11px;text-transform:uppercase;">Manager</th>
              <th style="padding:10px 12px;text-align:left;color:#64748B;font-weight:600;font-size:11px;text-transform:uppercase;">Status</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)

        # ── HR nudge actions ──
        manager_pending: dict[str, list[str]] = {}
        for e in pending_emps:
            m = e.get("manager_name") or e.get("manager") or "Unknown Manager"
            manager_pending.setdefault(m, []).append(e.get("name", "Unknown"))

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        section_header("🔔 Send Nudges", "Trigger notifications to managers for pending reviews")

        def _send_nudge(manager_name: str, employee_names: list[str]):
            pending_count = len(employee_names)
            msg = hr_agent.generate_completion_nudge(manager_name, pending_count)
            st.session_state["manager_notifications"].insert(
                0,
                {
                    "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "manager": manager_name,
                    "pending_count": pending_count,
                    "employees": employee_names,
                    "message": msg,
                },
            )
            st.success(f"Nudge sent to {manager_name} ({pending_count} pending reviews).")

        n1, n2 = st.columns([1, 2])
        with n1:
            if st.button("📣 Send Nudges to All", key="send_nudges_all", type="primary", use_container_width=True):
                for mgr, emps in manager_pending.items():
                    _send_nudge(mgr, emps)
        with n2:
            selected_mgr = st.selectbox(
                "Send to specific manager",
                list(manager_pending.keys()),
                key="pending_manager_select",
            )
            if st.button("Send Nudge", key="send_nudge_selected", use_container_width=True):
                _send_nudge(selected_mgr, manager_pending.get(selected_mgr, []))

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        for mgr, emps in manager_pending.items():
            c_mgr, c_count, c_btn = st.columns([2, 1, 1])
            with c_mgr:
                st.markdown(f"<div style='font-size:13px;color:#0F172A;font-weight:600;'>{escape(mgr)}</div>", unsafe_allow_html=True)
            with c_count:
                st.markdown(f"<div style='font-size:12px;color:#64748B;'>{len(emps)} pending</div>", unsafe_allow_html=True)
            with c_btn:
                if st.button("Notify", key=f"notify_{mgr}", use_container_width=True):
                    _send_nudge(mgr, emps)

        # Notification feed (simulated manager notifications)
        if st.session_state.get("manager_notifications"):
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            section_header("📨 Notification Feed", "Latest manager nudges sent by HR")
            feed_html = ""
            for n in st.session_state["manager_notifications"][:8]:
                feed_html += (
                    f"<div style='padding:10px 12px;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:8px;background:#FFFFFF;'>"
                    f"<div style='font-size:12px;color:#64748B;'>{n['ts']}</div>"
                    f"<div style='font-size:13px;font-weight:700;color:#0F172A;margin:2px 0;'>To: {escape(n['manager'])} · {n['pending_count']} pending</div>"
                    f"<div style='font-size:12px;color:#334155;'>{escape(n['message'])}</div>"
                    f"</div>"
                )
            st.markdown(f"<div class='piq-card'>{feed_html}</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-low">✅ All reviews have been submitted!</div>',
                    unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── SHARED: EMPLOYEE PROFILE RENDERER ───────────────────────
def _render_employee_profile(emp_id: str, editable: bool = True, show_generate: bool = True):
    emp    = cached_emp(emp_id)
    if not emp:
        st.error("Employee data not found.")
        return
    scores = data_agent.get_performance_score(emp)
    bias   = normalized_bias_risk(emp, scores)
    contribs = data_agent.detect_invisible_contributions(emp)

    col_left, col_mid, col_right = st.columns([1, 1, 1])

    # ── Left: raw data ──
    with col_left:
        section_header("📊 Performance Data")
        hr = emp.get("hr_data", {})
        jira = emp.get("jira_data", {})
        github = emp.get("github_data", {})
        confluence = emp.get("confluence_data", {})
        crm = emp.get("crm_data", {})

        def stat(label, value, good_threshold=None):
            color = "#0F172A"
            if good_threshold and isinstance(value, (int, float)):
                color = "#059669" if value >= good_threshold else "#D97706"
            st.markdown(
                f'<div class="stat-row">'
                f'<span class="stat-label">{label}</span>'
                f'<span class="stat-value" style="color:{color}">{value}</span>'
                f'</div>', unsafe_allow_html=True)

        st.markdown('<div class="piq-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">Jira</div>', unsafe_allow_html=True)
        stat("Tickets Closed", jira.get("tickets_closed", 0), 20)
        stat("On-Time Delivery", f"{jira.get('on_time_delivery_percent',0)}%", 80)
        stat("Sprint Velocity", jira.get("sprint_velocity_avg", 0), 6)
        stat("Bugs Against", jira.get("bugs_reported_against", 0))
        st.markdown('<div style="font-size:12px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.06em;margin:12px 0 8px;">GitHub</div>', unsafe_allow_html=True)
        stat("Commits", github.get("total_commits", 0), 20)
        stat("PRs Merged", github.get("prs_merged", 0), 4)
        stat("PR Reviews", github.get("prs_reviewed", 0), 8)
        st.markdown('<div style="font-size:12px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.06em;margin:12px 0 8px;">HR</div>', unsafe_allow_html=True)
        stat("Goals", f"{hr.get('goals_completed',0)}/{hr.get('goals_set',0)}")
        stat("Attendance", f"{hr.get('attendance_percentage',0)}%", 90)
        stat("Last Rating", f"{rating_to_10(hr.get('last_rating',0))}/10")
        if crm:
            st.markdown('<div style="font-size:12px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.06em;margin:12px 0 8px;">CRM (Sales)</div>', unsafe_allow_html=True)
            stat("Deals Closed", crm.get("deals_closed", 0), 10)
            stat("Revenue", f"₹{crm.get('revenue_generated',0):,}")
            stat("Conversion", f"{crm.get('conversion_rate',0)}%", 50)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Middle: radar + bias ──
    with col_mid:
        section_header("📈 AI Analysis")
        score_keys = ["delivery_score","quality_score","collaboration_score","documentation_score","goal_score"]
        labels = ["Delivery","Quality","Collaboration","Docs","Goals"]
        my_s   = [scores.get(k, 0) for k in score_keys]
        team_s = [TEAM_AVERAGES.get(k, 0) for k in score_keys]
        fig = radar_chart(my_s, team_s, labels)
        st.plotly_chart(fig, use_container_width=True)

        # Overall score card
        st.markdown(f"""
        <div class="piq-card" style="text-align:center;padding:16px;">
          <div class="score-big">{scores['overall_score']}</div>
          <div style="font-size:12px;color:#94A3B8;text-transform:uppercase;
                      letter-spacing:.06em;font-weight:600;">Overall Score / 10</div>
        </div>
        """, unsafe_allow_html=True)

        # Bias: show only after manager has submitted review.
        if bias.get("show_bias"):
            st.markdown(bias_alert_html(emp.get("name",""), bias), unsafe_allow_html=True)
        else:
            if st.session_state.get("user_role") == "HR":
                st.markdown(
                    '<div class="alert-low">ℹ️ Manager review not submitted yet. Bias comparison will appear after submission.</div>',
                    unsafe_allow_html=True,
                )

        # Invisible contributions
        if contribs:
            contrib_tags = "".join(f'<span class="contrib-tag">✨ {c}</span>' for c in contribs)
            st.markdown(f"""
            <div class="piq-card">
              <div style="font-size:13px;font-weight:700;color:#0F172A;margin-bottom:8px;">
                🌟 Invisible Contributions
              </div>
              <div>{contrib_tags}</div>
              <div style="font-size:11px;color:#94A3B8;margin-top:8px;">
                Often missed in traditional reviews
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Right: AI review ──
    with col_right:
        section_header("🤖 AI Review Draft")
        review_text_existing = (emp.get("review_text", "") or "").strip()
        manager_notes_existing = (emp.get("manager_notes", "") or "").strip()
        self_assessment_existing = (emp.get("self_assessment", "") or "").strip()
        review_status = emp.get("review_status", "")
        already_done = bool(review_text_existing) and is_manager_review_submitted(review_status)
        role = st.session_state.get("user_role", "")
        manager_submitted_review = bool(review_text_existing) and is_manager_review_submitted(review_status)

        # Managers should see employee self-assessment before writing review.
        if role == "Manager" and self_assessment_existing:
            st.markdown(
                "<div style='font-size:12px;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:4px 0 6px;'>Employee Self Assessment</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="review-box">{escape(self_assessment_existing)}</div>', unsafe_allow_html=True)

        # HR can only review/approve after manager has submitted a review.
        if role == "HR" and editable and not manager_submitted_review:
            st.markdown(
                '<div class="alert-low">ℹ️ Manager review is not submitted yet. HR review actions are locked until manager submission.</div>',
                unsafe_allow_html=True,
            )
        if already_done and role == "Manager":
            modify_msg = "You can modify it below." if editable else "View-only mode."
            st.markdown("""
            <div class="submit-success">
              <div style="font-weight:700;color:#059669;font-size:14px;">✅ Review Submitted</div>
              <div style="font-size:12px;color:#64748B;margin-top:2px;">__MODIFY_MSG__</div>
            </div>
            """.replace("__MODIFY_MSG__", modify_msg), unsafe_allow_html=True)

        if role == "HR":
            section_header("🧾 HR Review")
            manager_visible_text = review_text_existing or manager_notes_existing
            current_status = emp.get("review_status", "pending")
            if current_status == "approved_by_hr":
                st.markdown('<div class="submit-success"><div style="font-weight:700;color:#059669;">✅ HR Review Approved & Published</div></div>', unsafe_allow_html=True)
            elif current_status == "completed":
                st.markdown('<div class="alert-medium">🕒 Manager review submitted. HR decision pending.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-low">ℹ️ Waiting for manager review submission.</div>', unsafe_allow_html=True)
            if not manager_submitted_review:
                st.info("Manager review is not submitted yet. HR can review after manager submission.")
            else:
                st.markdown(
                    "<div style='font-size:12px;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:4px 0 6px;'>Manager Submitted Review</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="review-box">{escape(manager_visible_text)}</div>', unsafe_allow_html=True)

                hr_edit_key = f"hr_editing_{emp_id}"
                if hr_edit_key not in st.session_state:
                    st.session_state[hr_edit_key] = False
                if current_status == "approved_by_hr":
                    if st.button("✏️ Modify HR Review", key=f"hr_modify_{emp_id}"):
                        st.session_state[hr_edit_key] = True
                        st.rerun()

                feedback_val = st.text_area(
                    "HR Feedback (visible to employee)",
                    value=emp.get("approval_feedback", ""),
                    height=110,
                    key=f"hr_feedback_{emp_id}",
                    disabled=(current_status == "approved_by_hr" and not st.session_state[hr_edit_key]),
                )
                notes_val = st.text_area(
                    "HR Internal Notes",
                    value=emp.get("hr_notes", ""),
                    height=90,
                    key=f"hr_notes_{emp_id}",
                    disabled=(current_status == "approved_by_hr" and not st.session_state[hr_edit_key]),
                )
                h1, h2 = st.columns(2)
                with h1:
                    is_approved_locked = current_status == "approved_by_hr" and not st.session_state[hr_edit_key]
                    if is_approved_locked:
                        st.button("✅ Already Approved", key=f"hr_approved_state_{emp_id}", disabled=True, use_container_width=True)
                    approve_label = "💾 Save HR Modifications" if (current_status == "approved_by_hr" and st.session_state[hr_edit_key]) else "✅ Approve & Publish"
                    if (not is_approved_locked) and st.button(approve_label, key=f"hr_approve_{emp_id}", type="primary", use_container_width=True):
                        emp["approval_feedback"] = feedback_val.strip()
                        emp["hr_notes"] = notes_val.strip()
                        emp["hr_approved"] = True
                        emp["review_status"] = "approved_by_hr"
                        emp["hr_approved_timestamp"] = datetime.now().isoformat(timespec="seconds")
                        save_employee(emp)
                        st.session_state[hr_edit_key] = False
                        manager_id = _user_id_by_name(emp.get("manager", ""))
                        push_notification(
                            [emp_id, manager_id],
                            f"HR approved and published review for {emp.get('name','Employee')}.",
                            kind="approval",
                            actor_id=st.session_state.get("user_id", ""),
                        )
                        st.success("HR approval submitted and notifications sent.")
                        st.rerun()
                with h2:
                    if st.button("↩ Request Manager Rework", key=f"hr_rework_{emp_id}", use_container_width=True):
                        emp["approval_feedback"] = feedback_val.strip()
                        emp["hr_notes"] = notes_val.strip()
                        emp["hr_approved"] = False
                        emp["review_status"] = "completed"
                        emp["hr_approved_timestamp"] = None
                        save_employee(emp)
                        st.session_state[hr_edit_key] = False
                        manager_id = _user_id_by_name(emp.get("manager", ""))
                        push_notification(
                            [manager_id, emp_id],
                            f"HR requested manager rework for {emp.get('name','Employee')} review.",
                            kind="rework",
                            actor_id=st.session_state.get("user_id", ""),
                        )
                        st.success("Rework request saved and notifications sent.")
                        st.rerun()

        if show_generate and role == "Manager":
            key_gen = f"gen_review_{emp_id}"
            key_draft = f"draft_{emp_id}"
            key_edit  = f"editing_{emp_id}"
            hr_locked = role == "HR" and not manager_submitted_review
            can_edit = editable and (not already_done or st.session_state.get(key_edit, False)) and not hr_locked

            if st.button("🤖 Generate with Gemini", key=key_gen, disabled=(not editable) or hr_locked):
                with st.spinner("✨ Gemini is thinking..."):
                    try:
                        result = manager_agent.generate_draft_review(emp_id)
                        st.session_state[key_draft] = result
                        # Keep slider synced with latest AI recommendation.
                        st.session_state[f"rat_{emp_id}"] = float(
                            min(10.0, max(1.0, rating_to_10(result.get("recommended_rating", 7.0))))
                        )
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

            draft = st.session_state.get(key_draft)
            default_text = review_text_existing if review_text_existing else (draft.get("review_text","") if draft else "")

            if default_text or draft:
                review_text = st.text_area("Review Text", value=default_text, height=180,
                                            disabled=not can_edit, key=f"rt_{emp_id}")
                default_rating = (
                    rating_to_10(emp.get("final_rating", 0))
                    if emp.get("final_rating") is not None
                    else rating_to_10((draft or {}).get("recommended_rating", 7.0))
                )
                rating = st.slider(
                    "Rating (out of 10)",
                    min_value=1.0,
                    max_value=10.0,
                    step=0.5,
                    value=float(min(10.0, max(1.0, default_rating))),
                    key=f"rat_{emp_id}",
                )
                st.caption(
                    f"Overall score: {scores.get('overall_score', 0):.2f}/10 | "
                    f"AI recommended rating: {rating_to_10((draft or {}).get('recommended_rating', default_rating)):.1f}/10"
                )
                if editable and can_edit:
                    if st.button("✅ Submit Review", key=f"sub_{emp_id}", type="primary"):
                        action = "updated" if already_done else "submitted"
                        emp["review_text"]      = review_text
                        emp["final_rating"]     = float(rating)
                        emp["review_status"]    = "completed"
                        emp["review_timestamp"] = datetime.now().isoformat(timespec="seconds")
                        save_employee(emp)
                        push_notification(
                            [emp_id, "HR001"],
                            f"Manager {action} review for {emp.get('name','Employee')}.",
                            kind="review",
                            actor_id=st.session_state.get("user_id", ""),
                        )
                        st.session_state[key_edit] = False
                        st.success(f"✅ Review {action} for {emp.get('name','')} and notifications sent.")
                        st.balloons()
                        st.rerun()

                if already_done and editable:
                    if st.button("✏️ Modify Review", key=f"mod_{emp_id}"):
                        st.session_state[key_edit] = True
                        st.rerun()

                if draft and not editable:
                    st.markdown(f'<div class="review-box">{escape(default_text)}</div>',
                                unsafe_allow_html=True)

        # No duplicate manager-review rendering block here.


# ── MANAGER: DASHBOARD ───────────────────────────────────────
def manager_dashboard():
    mgr_id   = st.session_state["user_id"]
    mgr_prof = data_agent.get_employee_by_id(mgr_id)
    team     = manager_team_members(mgr_id)
    page_header("Manager Dashboard",
                f"Your team · {len([m for m in team if not is_manager_review_submitted(m.get('review_status',''))])} reviews pending")

    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)

    # Manager own card
    if mgr_prof:
        ms = data_agent.get_performance_score(mgr_prof)
        dept_color = DEPT_COLORS.get(mgr_prof.get("department",""), "#7C3AED")
        st.markdown(f"""
        <div class="piq-card" style="border-left:4px solid {dept_color};">
          <div style="display:flex;align-items:center;gap:12px;">
            {avatar_html(mgr_prof['name'], dept_color, 42)}
            <div style="flex:1;">
              <div class="piq-card-title">Your Profile: {mgr_prof['name']}</div>
              <div class="piq-card-sub">{mgr_prof['role']} · {mgr_prof['department']}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:28px;font-weight:800;color:{dept_color};">{ms['overall_score']}</div>
              <div style="font-size:11px;color:#94A3B8;">/ 10</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Team overview cards
    section_header("👥 Your Team", "Performance overview")
    if not team:
        st.info("No team members assigned.")
    else:
        cols = st.columns(min(len(team), 3))
        for i, member in enumerate(team):
            sc = data_agent.get_performance_score(member)
            status = member.get("review_status", "pending")
            s_badge = badge("Completed", "green") if is_manager_review_submitted(status) else badge("Pending", "amber")
            score_color = "#059669" if sc["overall_score"] >= 7 else "#D97706" if sc["overall_score"] >= 5 else "#DC2626"
            with cols[i % 3]:
                st.markdown(f"""
                <div class="piq-card">
                  <div style="display:flex;justify-content:space-between;align-items:start;">
                    <div>
                      <div class="piq-card-title">{member['name']}</div>
                      <div class="piq-card-sub">{member['role']}</div>
                      <div style="margin-top:8px;">{s_badge}</div>
                    </div>
                    <div style="text-align:right;">
                      <div style="font-size:26px;font-weight:800;color:{score_color};">{sc['overall_score']}</div>
                      <div style="font-size:10px;color:#94A3B8;">/ 10</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # Team chart
        names  = [m["name"] for m in team]
        scores = [data_agent.get_performance_score(m)["overall_score"] for m in team]
        fig = team_bar_chart(names, scores)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── MANAGER: WRITE REVIEWS ───────────────────────────────────
def manager_write_reviews():
    mgr_id = st.session_state["user_id"]
    team   = manager_team_members(mgr_id)
    page_header("Write Reviews", "Generate AI-powered reviews for your team")
    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)

    if not team:
        st.info("No team members assigned.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    sel = st.selectbox("Select Team Member", [m["employee_id"] for m in team],
                       format_func=lambda eid: f"{eid} · {cached_emp(eid).get('name','')}",
                       key="mgr_review_select")
    if sel:
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        _render_employee_profile(sel, editable=True, show_generate=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── EMPLOYEE: DASHBOARD ──────────────────────────────────────
def employee_dashboard():
    uid = st.session_state["user_id"]
    emp = data_agent.get_employee_by_id(uid)
    page_header(f"Welcome back, {st.session_state['user_name'].split()[0]}! 👋",
                f"{st.session_state['user_jobtitle']} · {st.session_state['user_dept']} · Q1 2026")
    if not emp:
        st.error("Profile not found.")
        return

    scores   = data_agent.get_performance_score(emp)
    contribs = data_agent.detect_invisible_contributions(emp)
    hr       = emp.get("hr_data", {})
    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)

    # ── Score + rank ──
    all_scores = sorted([s.get("overall_score", 0.0) for s in cached_scores_map().values()], reverse=True)
    rank = all_scores.index(scores["overall_score"]) + 1 if scores["overall_score"] in all_scores else "-"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card(str(scores["overall_score"]), "Overall Score", "#7C3AED", "Out of 10"),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(f"#{rank}", "Team Rank", "#2563EB", f"of {len(all_scores)} employees"),
                    unsafe_allow_html=True)
    with c3:
        goals_done = hr.get("goals_completed", 0)
        goals_set  = hr.get("goals_set", 1)
        goal_pct   = int(goals_done / goals_set * 100) if goals_set else 0
        gcolor = "#059669" if goal_pct >= 75 else "#D97706"
        st.markdown(metric_card(f"{goals_done}/{goals_set}", "Goals Completed", gcolor, f"{goal_pct}% complete"),
                    unsafe_allow_html=True)
    with c4:
        att = hr.get("attendance_percentage", 0)
        acolor = "#059669" if att >= 90 else "#D97706"
        st.markdown(metric_card(f"{att}%", "Attendance", acolor, "This quarter"),
                    unsafe_allow_html=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ── Charts row ──
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        score_keys = ["delivery_score","quality_score","collaboration_score","documentation_score","goal_score"]
        labels = ["Delivery","Quality","Collaboration","Docs","Goals"]
        my_s   = [scores.get(k, 0) for k in score_keys]
        team_s = [TEAM_AVERAGES.get(k, 0) for k in score_keys]
        fig = radar_chart(my_s, team_s, labels, "Your Scores vs Team Average")
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        fig2 = score_trend_chart(st.session_state["user_name"])
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Score bars ──
    section_header("📊 Dimension Breakdown", "Your score vs team average")
    dim_colors = {
        "Delivery":"#7C3AED","Quality":"#2563EB",
        "Collaboration":"#059669","Documentation":"#D97706","Goals":"#0891B2",
    }
    for key, label in zip(score_keys, labels):
        val  = scores.get(key, 0.0)
        tavg = TEAM_AVERAGES.get(key, 0.0)
        col  = dim_colors.get(label, "#7C3AED")
        diff = round(val - tavg, 1)
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        diff_col = "#059669" if diff >= 0 else "#DC2626"
        c_a, c_b = st.columns([4, 1])
        with c_a:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
              <span style="font-size:13px;font-weight:600;color:#0F172A;">{label}</span>
              <span style="font-size:13px;color:#64748B;">{val}/10
                <span style="color:{diff_col};font-weight:700;margin-left:6px;">{diff_str} vs avg</span>
              </span>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(max(val / 10.0, 0.0), 1.0))
        with c_b:
            st.markdown(f'<div style="font-size:11px;color:#94A3B8;margin-top:4px;">Team: {tavg}</div>',
                        unsafe_allow_html=True)

    # ── Invisible contributions ──
    if contribs:
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        section_header("🌟 Your Invisible Contributions", "These often go unnoticed — highlight them!")
        tags = "".join(f'<span class="contrib-tag">✨ {c}</span>' for c in contribs)
        st.markdown(f"""
        <div class="piq-card">
          <div style="margin-bottom:10px;">{tags}</div>
          <div style="font-size:12px;color:#94A3B8;">
            💡 Make sure to mention these in your self assessment — they matter!
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── EMPLOYEE: SELF ASSESSMENT ────────────────────────────────
def employee_self_assessment():
    uid = st.session_state["user_id"]
    emp = data_agent.get_employee_by_id(uid)
    page_header("Self Assessment", "AI-assisted — edit and submit your own words")
    if not emp:
        return

    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)
    # Allow employees to update self-assessment until HR final approval.
    locked = bool(emp.get("hr_approved", False))
    existing = emp.get("self_assessment", "").strip()
    already_submitted = bool(existing)

    if already_submitted:
        st.markdown("""
        <div class="submit-success">
          <div style="font-weight:700;color:#059669;font-size:14px;">✅ Self Assessment Submitted</div>
          <div style="font-size:12px;color:#64748B;margin-top:2px;">
            You can edit and resubmit anytime while review is pending.
          </div>
        </div>
        """, unsafe_allow_html=True)

    draft_key = f"self_draft_{uid}"
    text_key = f"self_text_area_{uid}"
    if text_key not in st.session_state:
        st.session_state[text_key] = existing

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🤖 Generate Draft with Gemini", disabled=locked, key="gen_self"):
            with st.spinner("✨ Gemini is crafting your self assessment..."):
                try:
                    draft = employee_agent.generate_self_assessment(uid)
                    st.session_state[draft_key] = draft
                    st.session_state[text_key] = draft
                    st.success("Draft generated. You can edit it before submitting.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation failed: {e}")
    with col2:
        if st.session_state.get(draft_key) and st.button("🔄 Regenerate", key="regen_self"):
            del st.session_state[draft_key]
            st.session_state[text_key] = ""
            st.rerun()

    text = st.text_area(
        "Your Self Assessment", height=280,
        disabled=locked, key=text_key,
        placeholder="Click 'Generate Draft with Gemini' to get an AI-powered draft, then edit it in your own words.",
    )

    char_count = len(text) if text else 0
    st.markdown(f'<div style="font-size:11px;color:#94A3B8;text-align:right;">{char_count} characters</div>',
                unsafe_allow_html=True)

    if not locked:
        if st.button("✅ Submit Self Assessment", type="primary", key="submit_self"):
            if not text.strip():
                st.warning("Please write or generate a self assessment before submitting.")
            else:
                emp["self_assessment"] = text.strip()
                # Do not downgrade completed reviews back to self_assessed.
                if emp.get("review_status") == "pending":
                    emp["review_status"] = "self_assessed"
                save_employee(emp)
                st.session_state[draft_key] = text
                st.success("✅ Self assessment submitted successfully!")
                st.balloons()
                st.rerun()

    if locked:
        st.info("Self assessment is locked after HR final approval.")

    st.markdown("</div>", unsafe_allow_html=True)


# ── EMPLOYEE: FEEDBACK ───────────────────────────────────────
def employee_feedback():
    uid = st.session_state["user_id"]
    emp = data_agent.get_employee_by_id(uid)
    page_header("My Feedback", "Your performance review result")
    if not emp:
        return

    st.markdown("<div class='piq-content'>", unsafe_allow_html=True)
    status = emp.get("review_status", "pending")

    hr_approved = bool(emp.get("hr_approved", False))
    review_text = emp.get("review_text", "").strip()
    approval_feedback = emp.get("approval_feedback", "").strip()

    if not hr_approved:
        if status == "pending":
            icon, title, body, cls = (
                "⏳", "Review Pending",
                f"Your manager (<b>{emp.get('manager_name') or emp.get('manager') or 'your manager'}</b>) hasn't submitted your review yet. "
                "Check back soon.",
                "alert-medium"
            )
        elif status in ("completed", "self_assessed"):
            icon, title, body, cls = (
                "📋", "Review Submitted — Awaiting HR Approval",
                "Your manager has submitted the review. HR is reviewing it. You'll see the feedback once approved.",
                "alert-medium"
            )
        else:
            icon, title, body, cls = ("ℹ️", "Status Unknown", "", "alert-low")
        st.markdown(f"""
        <div class="{cls}">
          <div style="font-weight:700;font-size:15px;color:#0F172A;margin-bottom:6px;">{icon} {title}</div>
          <div style="font-size:13px;color:#64748B;">{body}</div>
        </div>
        """, unsafe_allow_html=True)

        # Show manager review once submitted, even before HR approval.
        if review_text:
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            section_header("📝 Manager Review")
            st.markdown(f'<div class="review-box">{escape(review_text)}</div>',
                        unsafe_allow_html=True)
        elif status in ("completed", "self_assessed"):
            st.info("Review is submitted but text is not available yet. Please ask HR/Manager to re-save it.")

        # If HR has provided comments but not finalized flag yet, still show them.
        if approval_feedback:
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            section_header("💬 HR Feedback")
            st.markdown(f'<div class="piq-card">{escape(approval_feedback)}</div>',
                        unsafe_allow_html=True)
    else:
        rating = rating_to_10(emp.get("final_rating", 0))
        band   = emp.get("recommended_band", "Meets Expectations")

        st.markdown(f"""
        <div class="alert-low" style="margin-bottom:20px;">
          <div style="font-weight:700;font-size:15px;color:#065F46;margin-bottom:4px;">
            ✅ Your Review is Ready!
          </div>
          <div style="font-size:13px;color:#047857;">HR has approved your performance review.</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(metric_card(
                f"{rating}/10", "Final Rating", "#7C3AED",
                "Standardized scale"
            ), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card(band, "Performance Band", "#059669", ""),
                        unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        section_header("📝 Manager Review")
        if review_text:
            st.markdown(f'<div class="review-box">{escape(review_text)}</div>',
                        unsafe_allow_html=True)
        else:
            st.info("Review text not available.")

        if approval_feedback:
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            section_header("💬 HR Feedback")
            st.markdown(f'<div class="piq-card">{escape(approval_feedback)}</div>',
                        unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── ROUTER ───────────────────────────────────────────────────
def render():
    role = st.session_state["user_role"]
    page = st.session_state.get("page", "Dashboard")

    if role == "HR":
        if page == "Reports":
            hr_reports()
        else:
            hr_dashboard()

    elif role == "Manager":
        if page == "Write Reviews":
            manager_write_reviews()
        else:
            manager_dashboard()

    elif role == "Employee":
        if page == "Self Assessment":
            employee_self_assessment()
        elif page == "Feedback":
            employee_feedback()
        else:
            employee_dashboard()


# ── ENTRY POINT ──────────────────────────────────────────────
if not st.session_state.get("is_logged_in"):
    login_page()
else:
    sidebar()
    render()
