# Jira Test Case Generator (GROQ API)

A Streamlit web application that fetches Jira ticket details and generates comprehensive test case scenarios using GROQ LLM models via LangChain.

## Features

- Fetch Jira ticket summary and description using Jira REST API
- Generate functional, negative, and edge-case test scenarios using GROQ LLM
- Display generated test cases as a formatted table in the browser
- Export test cases to Excel (.xlsx) with one-click download
- Supports multiple GROQ models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, `gemma2-9b-it`

## Prerequisites

- **Jira Cloud account** with API token (generate at https://id.atlassian.com/manage-profile/security/api-tokens)
- **GROQ API key** (get one at https://console.groq.com/keys)
- **Docker Desktop** (for Docker-based setup) or **Python 3.11+** (for local setup)

## Project Structure

```
jira/
├── app.py              # Main Streamlit application
├── Dockerfile          # Docker build configuration
├── requirements.txt    # Python dependencies
└── README.md
```

## Setup and Run

### Option 1: Docker (Recommended)

```bash
cd C:\capstone_ic_ik\edureka\jira
docker build -t jira-testcase-app .
docker run -p 8501:8501 jira-testcase-app
```

Open http://localhost:8501 in your browser.

### Option 2: Local Python

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. Open http://localhost:8501 in your browser
2. Enter the Jira ticket URL or ID (e.g., `KOK-354721`)
3. Provide your Jira Cloud URL, username (email), and API token
4. Paste your GROQ API key and select a model
5. Click **"Fetch & Generate Test Cases"**
6. Review the generated test cases and click **"Export Test Case"** to download as Excel

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web UI framework |
| pandas | Data manipulation and Excel export |
| openpyxl | Excel file writer engine |
| jira | Jira REST API client |
| langchain | LLM orchestration framework |
| langchain_core | Core LangChain components (prompts, parsers) |
| langchain_groq | GROQ LLM integration for LangChain |

## Troubleshooting

| Error | Solution |
|-------|----------|
| `AUTHENTICATED_FAILED` | Verify Jira email and API token are correct |
| `Invalid API Key` (GROQ) | Regenerate your GROQ API key at https://console.groq.com/keys |
| `model has been decommissioned` | Select a different model from the dropdown |
| `Issue does not exist` | Check the ticket ID and your Jira project permissions |
