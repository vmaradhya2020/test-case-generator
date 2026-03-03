# pip install streamlit pandas openpyxl jira atlassian-python-api langchain langchain_groq

import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- JIRA Import ---
from jira import JIRA

# --- Confluence Import ---
from atlassian import Confluence

# --- LangChain & GROQ Import (pip install langchain_groq) ---
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Streamlit Page Config ---
st.set_page_config(page_title="Jira/Confluence Test Case Generator (GROQ)", layout="wide")

def detect_url_type(url_input):
    """Detect if the input is a Jira ticket or Confluence page."""
    url_input = url_input.strip()
    if "/wiki/spaces/" in url_input or "/wiki/pages/" in url_input:
        return "confluence"
    elif "/browse/" in url_input or re.search(r"([A-Z][A-Z0-9]+-\d+)", url_input, re.IGNORECASE):
        return "jira"
    else:
        return "unknown"

def extract_ticket_id(jira_input):
    """Extract Jira ticket ID from URL or text."""
    match = re.search(r"([A-Z][A-Z0-9]+-\d+)", jira_input.strip(), re.IGNORECASE)
    return match.group(1) if match else None

def normalize_confluence_url(confluence_url):
    """Normalize Confluence URL by removing edit-v2 and fragments."""
    # Remove fragment identifier (e.g., #Youth-and-Child-Discount)
    confluence_url = confluence_url.split("#")[0]
    # Replace /edit-v2/ with /pages/
    confluence_url = confluence_url.replace("/edit-v2/", "/pages/")
    return confluence_url

def extract_confluence_page_id(confluence_url):
    """Extract Confluence page ID from URL."""
    # Normalize URL first
    confluence_url = normalize_confluence_url(confluence_url)
    # Pattern for URLs like /pages/4162551820/
    match = re.search(r"/pages/(\d+)", confluence_url)
    if match:
        return match.group(1)
    return None

def fetch_jira_issue(ticket_id, jira_url, jira_user, jira_token):
    """Fetch Jira issue details."""
    try:
        jira_options = {"server": jira_url}
        jira_client = JIRA(options=jira_options, basic_auth=(jira_user, jira_token))
        issue = jira_client.issue(ticket_id)
        return issue.fields.summary, (issue.fields.description or "")
    except Exception as e:
        return None, f"Error fetching JIRA issue: {str(e)}"

def fetch_confluence_page(page_id, confluence_url, confluence_user, confluence_token):
    """Fetch Confluence page content."""
    try:
        confluence = Confluence(
            url=confluence_url,
            username=confluence_user,
            password=confluence_token,
            cloud=True
        )
        page = confluence.get_page_by_id(page_id, expand="body.storage")
        title = page.get("title", "")
        # Get the HTML content and clean it up
        body_html = page.get("body", {}).get("storage", {}).get("value", "")
        # Strip HTML tags for cleaner text (basic approach)
        clean_text = re.sub(r'<[^>]+>', ' ', body_html)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return title, clean_text
    except Exception as e:
        return None, f"Error fetching Confluence page: {str(e)}"

def generate_test_cases_groq(content_title, content_description, groq_api_key, groq_model):
    try:
        # Create the LLM chain using the GROQ API and the chosen model
        # temperature = 0.0 => Deterministic (same output every time)
        # temperature = 0.2 => Some randomness
        # temperature = 1.0 => Very random/creative
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model=groq_model,
            temperature=0.0  
        )
        # Escape curly braces in content to avoid format string issues
        safe_title = content_title.replace("{", "{{").replace("}", "}}")
        safe_description = content_description.replace("{", "{{").replace("}", "}}")

        prompt = ChatPromptTemplate.from_messages([
            ("system",
                "You are an expert QA engineer. Write a thorough set of high-level functional, negative, and edge-case test scenarios given the content below. "
                "Number each scenario. Format the output as a markdown table with columns: Test Case ID, Scenario Title, Scenario Description, Expected results. Output only the table, no explanations."
            ),
            ("human", f"Title: {safe_title}\nDescription/Content: {safe_description}")
        ])
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({})
        return result
    except Exception as e:
        return f"*Error from GROQ API: {str(e)}*"

def parse_markdown_table(md_table):
    lines = [line for line in md_table.splitlines() if "|" in line and "---" not in line]
    if not lines:
        return pd.DataFrame()
    columns = [x.strip() for x in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[1:]:
        values = [x.strip() for x in line.strip("|").split("|")]
        if len(values) == len(columns):
            rows.append(values)
    return pd.DataFrame(rows, columns=columns)

st.title("🤖 Jira/Confluence Test Case Generator (GROQ API)")

st.markdown(
    """
    Enter a **JIRA ticket URL/ID** or **Confluence page URL** and your credentials below.
    The app will fetch the content, generate comprehensive GROQ LLM-based test scenarios, and let you export the result as Excel.

    **Supported URL formats:**
    - Jira: `https://your-domain.atlassian.net/browse/PROJECT-123` or just `PROJECT-123`
    - Confluence: `https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title`
    """
)

# --- API Key Help Section ---
with st.expander("How to get API Keys?"):
    st.markdown(
        """
        ### GROQ API Key
        1. Go to [GROQ Console](https://console.groq.com/keys)
        2. Sign up or log in to your account
        3. Click **"Create API Key"**
        4. Copy and paste the key here

        ### Atlassian API Token (for Jira & Confluence)
        1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
        2. Log in with your Atlassian account
        3. Click **"Create API token"**
        4. Give it a label (e.g., "Test Case Generator")
        5. Copy and paste the token here
        6. Use your **Atlassian email** as the username
        """
    )

# ---- Credential & Input Form ----
with st.form("jira_form", clear_on_submit=False):
    source_url = st.text_input(
        "Jira Ticket or Confluence Page URL",
        placeholder="e.g. https://rakutenmobile.atlassian.net/browse/KOK-354721 or Confluence wiki URL"
    )
    col1, col2 = st.columns(2)
    with col1:
        atlassian_url = st.text_input(
            "Atlassian Cloud URL",
            value="https://rakutenmobile.atlassian.net"
        )
        atlassian_user = st.text_input("Atlassian Username / Email")
        atlassian_token = st.text_input("Atlassian API Token", type="password")
        st.caption("Same credentials work for both Jira and Confluence.")
    with col2:
        groq_api_key = st.text_input(
            "GROQ API Key",
            type="password",
            placeholder="Paste your GROQ API key here"
        )
        groq_model = st.selectbox(
            "GROQ Model",
            options=[
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ],
            index=0
        )
        st.caption("See groq.com/docs for available models.")
    submitted = st.form_submit_button("Fetch & Generate Test Cases")

if submitted:
    # Validate credentials
    if not all([atlassian_url, atlassian_user, atlassian_token, groq_api_key, groq_model]):
        st.error("All credentials and API keys are required.")
        st.stop()

    # Detect URL type
    url_type = detect_url_type(source_url)

    if url_type == "jira":
        ticket_id = extract_ticket_id(source_url)
        if not ticket_id:
            st.error("Could not extract Jira ticket ID. Check your input.")
            st.stop()

        with st.spinner("Fetching ticket from Jira..."):
            content_title, content_description = fetch_jira_issue(ticket_id, atlassian_url, atlassian_user, atlassian_token)
        if not content_title:
            st.error(content_description)
            st.stop()
        st.success(f"Got Jira {ticket_id}: *{content_title}*")
        source_identifier = ticket_id

    elif url_type == "confluence":
        page_id = extract_confluence_page_id(source_url)
        if not page_id:
            st.error("Could not extract Confluence page ID. Check your input URL.")
            st.stop()

        with st.spinner("Fetching page from Confluence..."):
            content_title, content_description = fetch_confluence_page(page_id, atlassian_url, atlassian_user, atlassian_token)
        if not content_title:
            st.error(content_description)
            st.stop()
        st.success(f"Got Confluence page: *{content_title}*")
        source_identifier = f"Confluence_{page_id}"

    else:
        st.error("Could not determine URL type. Please provide a valid Jira ticket URL/ID or Confluence page URL.")
        st.stop()

    with st.spinner(f"Contacting GROQ LLM '{groq_model}' to generate test cases..."):
        test_case_md = generate_test_cases_groq(content_title, content_description, groq_api_key, groq_model)
    if test_case_md.startswith("*Error"):
        st.error(test_case_md)
        st.stop()

    st.markdown("---")
    st.header("Generated Test Case Scenarios")
    st.markdown(test_case_md)
    df = parse_markdown_table(test_case_md)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No valid table detected; review LLM output.")

    output_filename = f"Test_cases_{source_identifier}.xlsx"
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Test Cases")
    buffer.seek(0)
    st.download_button(
        "Export Test Case",
        data=buffer,
        file_name=output_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.caption("Review all generated scenarios for relevance and coverage before using in production.")

# --- Final Tips ---
st.info("Never hard-code production secrets! Use Streamlit secrets or environment variables for all API keys and tokens.")

