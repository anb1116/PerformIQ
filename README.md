# PerformIQ — Agentic Performance Layer for effiHR

## 🧠 What is PerformIQ?
PerformIQ is an agentic AI layer designed to make performance appraisals faster, fairer, and more data-driven for modern teams. Instead of relying only on subjective manager memory at review time, PerformIQ consolidates objective signals from multiple work systems (Jira, GitHub, Confluence, HR metrics, and collaboration indicators) into unified employee performance profiles.

Built for the `effiHR` context, PerformIQ introduces role-aware intelligence through specialized agents that support HR teams, managers, and employees in different ways. HR gets cycle-level risk and completion visibility, managers get data-backed draft reviews and nudges, and employees get coaching support for clearer self-assessments. The result is a transparent, measurable, and scalable performance process that improves review quality without adding process overhead.

## 🏗️ Architecture
```text
Data Sources (Jira/GitHub/Confluence/HR)
        ↓
Data Aggregator Agent
        ↓
HR Orchestrator Agent
    ↙           ↘
Manager          Employee
Assistant        Coach
Agent            Agent
        ↓
Streamlit Dashboard
```

## 👥 The 4 Agents
- **Data Aggregator Agent**: Converts raw activity data into normalized performance dimensions and benchmarking signals.
- **Manager Assistant Agent**: Drafts fair, metric-cited manager reviews and reminder nudges with clear rating suggestions.
- **Employee Coach Agent**: Guides employees with self-assessment drafts, progress alerts, and clear rating explanations.
- **HR Orchestrator Agent**: Provides cycle governance, bias diagnostics, department analytics, and executive summaries.

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- Ollama installed ([ollama.com](https://ollama.com))
- Llama 3.2:3b model

### Step 1 — Clone the repo
```bash
git clone [your-repo-url]
cd performiq
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Pull Llama model
```bash
ollama pull llama3.2:3b
```

### Step 4 — Generate fake data
```bash
python data/generate_data.py
```

### Step 5 — Run the app
```bash
streamlit run app.py
```

### Step 6 — Open browser
Go to [http://localhost:8501](http://localhost:8501)

## 🎯 Features
- 🧠 **Agentic architecture** with 4 dedicated AI agents for HR, managers, employees, and data intelligence
- 📊 **Unified scoring engine** across Delivery, Quality, Collaboration, Documentation, and Goals
- ⚖️ **Bias risk detection** at employee and manager-pattern levels
- 🧩 **Role-aware logic** so engineering, sales, operations, HR, and product are evaluated with relevant signals
- 🚨 **HR command center** with completion tracking, risk alerts, and department analytics
- 👔 **Manager draft reviews** with structured, data-cited output and recommended rating/band
- 🙋 **Employee coaching tools** for self-assessment writing, progress alerts, and rating explanations
- 🏷️ **Invisible contribution detection** (peer reviews, knowledge sharing, collaboration support)
- 📧 **Automated nudge generation** for pending reviews and cycle adherence
- ✨ **Professional Streamlit UX** with interactive charts, cards, and action workflows

## 📊 Success Metrics
| Metric | Before | After |
|---|---:|---:|
| Review completion visibility | Manual follow-ups | Real-time dashboard tracking |
| Time to draft manager review | 20-30 min average | 2-5 min AI-assisted |
| Data coverage in reviews | Inconsistent | Standardized multi-source evidence |
| Bias signal detection | Ad-hoc, retrospective | Built-in proactive alerts |
| Employee self-assessment quality | Variable | Guided, metric-backed drafts |
| HR cycle reporting effort | Spreadsheet-heavy | One-click executive summary |

## 🛠️ Tech Stack
- **Language**: Python
- **Frontend/UI**: Streamlit
- **AI Runtime**: Ollama
- **LLM**: Llama 3.2:3b
- **Data Processing**: Pandas
- **Visualization**: Plotly (Express + Graph Objects)
- **Storage**: JSON-based local data files
- **Orchestration Pattern**: Multi-agent architecture

## 📁 Project Structure
```text
performiq/
├── agents/
│   ├── data_agent.py
│   ├── employee_agent.py
│   ├── hr_agent.py
│   └── manager_agent.py
├── data/
│   ├── generate_data.py
│   ├── company_summary.json
│   ├── EMP001.json
│   ├── EMP002.json
│   ├── EMP003.json
│   ├── EMP004.json
│   ├── EMP005.json
│   ├── EMP006.json
│   ├── EMP007.json
│   ├── EMP008.json
│   ├── EMP009.json
│   └── EMP010.json
├── app.py
├── requirements.txt
└── README.md
```

---

# FINAL STEP — How to Run Everything

Once all prompts are done, run in CMD inside your `eff` folder:

```bash
cd performiq
python data/generate_data.py
streamlit run app.py
```

---

## Order to Follow

| Step | Prompt | Do After |
|---|---|---|
| 1 | Project Structure | Immediately |
| 2 | Generate Data | Run `python data/generate_data.py` |
| 3 | Data Agent | Run `python agents/data_agent.py` to test |
| 4 | Manager Agent | Run `python agents/manager_agent.py` to test |
| 5 | Employee Agent | Run `python agents/employee_agent.py` to test |
| 6 | HR Agent | Run `python agents/hr_agent.py` to test |
| 7 | Streamlit App | Run `streamlit run app.py` |
| 8 | README | Last thing before GitHub push |
