# PerformIQ - Agentic Performance Intelligence

PerformIQ is a Streamlit application for role-based performance review operations across HR, managers, and employees.
It combines deterministic scoring, AI-assisted drafting, and workflow controls to run review cycles with speed, clarity, and fairness.

## Project Upgrade Summary (For PPT)

### Problem Statement

- Review workflows were inconsistent across roles (HR and manager actions overlapped).
- Mixed score scales (`/5` and `/10`) caused confusing outputs and wrong comparisons.
- Advanced analytics showed non-human-readable/nested output and stale interpretation.
- UI had readability issues (white-on-white / low contrast in alerts and cards).
- State transitions (submit/approve/rework) were not visibly reflected in some screens.
- No unified notification layer existed for HR, Manager, Employee updates.

### What We Built

- End-to-end workflow separation:
  - Employee self-assessment
  - Manager review drafting/submission
  - HR review/approval/rework/modification
- Unified scoring model on `/10` across UI and backend logic.
- Structured table rendering for advanced analytics outputs.
- Performance + reliability hardening:
  - cache wrappers
  - resilient Gemini config (timeouts/retries/fallback)
  - defensive data loading for non-employee JSON files
- Persistent in-app notification center for all roles.

### Business Impact

- Faster review cycle handling through clear role-specific actions.
- Better trust in outputs due to deterministic + correctly scaled analytics.
- Reduced workflow confusion with explicit status banners and pipeline table.
- Improved demo readiness with professional UI and readable outputs.

## Current Architecture

### App Layer

- `app.py`
  - Role routing: HR / Manager / Employee
  - UI workflows and state transitions
  - Status banners, review pipeline tracker, notifications panel
  - Advanced analytics actions and structured rendering

### Agent Layer (`agents/`)

- `data_agent.py`
  - employee data loading
  - performance score engine
  - bias and contribution detectors
  - robust filtering of non-employee/system JSON files
- `manager_agent.py`
  - manager draft generation and recommended rating/band
- `employee_agent.py`
  - self-assessment and coaching generation helpers
- `hr_agent.py`
  - HR dashboard and executive-level summary helpers
- `intelligence_agent.py`
  - normalized analytics dataset + action router
- `llm_config.py`
  - Gemini wrapper with retries, timeout and fallback handling

## Workflow Pipeline

1. Employee submits self-assessment.
2. Manager generates/edits/submits review (`review_status=completed`).
3. HR reviews manager submission:
   - Approve & Publish (`review_status=approved_by_hr`)
   - Request Manager Rework
   - Modify HR review post-approval
4. Employee sees manager and HR feedback as status evolves.

## Advanced Analytics Pipeline

`HR Reports` executes:

- `build_employee_dataset()`
- `run_analysis(action, data)`

Actions:

- `bias_hotspots`
- `weekly_digest`
- `manager_risk_scorecard`
- `priority_queue`
- `rebalance_recommendations`
- `manager_bias_explainer`
- `weekly_hr_action_plan`
- `invisible_top_performer_detection`

Output contract:

```json
{
  "title": "Module Name",
  "insights": [],
  "recommendations": []
}
```

## Notifications

- Stored in `data/_notifications.json`
- Displayed per logged-in user in sidebar
- Triggered on:
  - manager submit/modify
  - HR approve/publish
  - HR rework request
  - HR modification save

## Tech Stack

- Python
- Streamlit
- Plotly
- Google Gemini (`google-generativeai`)
- `python-dotenv`
- Local JSON data store

## Setup

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key
```

### 3) (Optional) Refresh sample data

```bash
python data/generate_data.py
```

### 4) Run app

```bash
python -m streamlit run app.py
```

Open: [http://localhost:8501](http://localhost:8501)
