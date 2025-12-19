'''import os
from crewai import Agent, LLM
from tools import get_search_tool
from dotenv import load_dotenv
from config import MAX_AGE_DAYS, MAX_INCIDENTS

load_dotenv()

llm = LLM(
    provider="google",
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Agent 1: Researcher – focus is on harm-causing incidents
researcher = Agent(
    role="AI Ethics & Incident Scout",
    goal=(
        f"Find up to {MAX_INCIDENTS} recent (≤{MAX_AGE_DAYS} days) real-world "
        "incidents where AI caused harm. Focus on credible news, not studies or opinions."
    ),
    backstory="""
    You are an expert in ethical AI and responsible technology with a background in investigative
    journalism. Your mission is to scour the web for public reports and credible news stories
    detailing AI-related misconduct and failures (e.g., scams, bias, deepfakes, fraud, accidents).
    You provide the initial intelligence that the team will then analyze and verify.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[get_search_tool()],
    allow_delegation=False
)

# Agent 2: Analyst – validate and enrich each harmful incident
analyst = Agent(
    role="AI Incident Analyst",
    goal="""
    Validate and enrich the incidents provided by the Researcher. For each incident:
    - Confirm accuracy using at least three credible sources.
    - Extract details about the impact, estimated financial loss, and any fines or penalties.
    - Mark any missing numeric data as 'unknown'.
    """,
    backstory="""
    You are a meticulous fact-checker and financial analyst. You cross-verify information from multiple
    reputable sources and ensure accuracy of all details about AI harm.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[get_search_tool()],
    allow_delegation=False
)

# Agent 3: Reporter – produce the final JSON report
reporter = Agent(
    role="AI Incident Reporter",
    goal="""
    Synthesize the validated findings from the Analyst into a clear, concise, and well-structured JSON report.
    Each report must include: title, summary, impact, estimated_loss ('unknown' if missing), fine_due_to_non_compliance ('unknown' if missing), and a list of verified sources.
    """,
    backstory="""
    You are a professional technical writer specializing in data journalism. You transform complex verified data into an easily digestible structured JSON format.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[],  # The Reporter synthesizes information only
    allow_delegation=False
)'''
'''
import os
from crewai import Agent, LLM
from tools import get_search_tool
from dotenv import load_dotenv
from config import MAX_AGE_DAYS, MAX_INCIDENTS, MIN_SOURCES, SEARCH_TOOL

load_dotenv()

# LLM backend
llm = LLM(
    provider="google",
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Agent 1: Researcher – focus is on harmful incidents
researcher = Agent(
    role="AI Ethics & Incident Scout",
    goal=(
        f"Find up to {MAX_INCIDENTS} recent (≤{MAX_AGE_DAYS} days) "
        "real-world incidents where AI caused harm. Focus on credible news, not studies or opinions."
    ),
    backstory="""
    You are an expert in ethical AI and investigative journalism.
    Your mission is to collect public reports and credible news stories
    detailing AI-related misconduct and failures (e.g., scams, bias, deepfakes, fraud, accidents).
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[get_search_tool(SEARCH_TOOL)],  # ✅ uses hybrid
    allow_delegation=False,
)

# Agent 2: Analyst – validate & enrich each harmful incident
analyst = Agent(
    role="AI Incident Analyst",
    goal=(
        f"Validate and enrich incidents from the Researcher. "
        f"Confirm accuracy using ≥{MIN_SOURCES} credible sources. "
        f"Extract impact, estimated financial loss, and fines (use 'unknown' if missing)."
    ),
    backstory="""
    You are a meticulous fact-checker and analyst.
    You cross-verify incidents using multiple reputable sources
    and ensure accuracy of details about AI harm.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[get_search_tool(SEARCH_TOOL)],  # ✅ uses hybrid
    allow_delegation=False,
)

# Agent 3: Reporter – produce structured JSON
reporter = Agent(
    role="AI Incident Reporter",
    goal="""
    Synthesize the validated incidents into a clear, concise JSON report.
    Each report must include:
    - title
    - summary
    - impact
    - estimated_loss ('unknown' if missing)
    - fine_due_to_non_compliance ('unknown' if missing)
    - sources (list of verified URLs, ≥2)
    """,
    backstory="""
    You are a professional technical writer specializing in structured data journalism.
    You transform verified incident data into JSON for reporting.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[],  # Reporter doesn’t need search tools
    allow_delegation=False,
)
'''

import os
from crewai import Agent, LLM
from tools import get_search_tool
from dotenv import load_dotenv
from config import MAX_AGE_DAYS, MAX_INCIDENTS, MIN_SOURCES, SEARCH_TOOL

load_dotenv()

# LLM backend
llm = LLM(
    provider="google",
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Agent 1: Researcher – focus is on harmful incidents
researcher = Agent(
    role="AI Ethics & Incident Scout",
    goal=(
        f"Find up to {MAX_INCIDENTS} recent (≤{MAX_AGE_DAYS} days) "
        "real-world incidents where AI caused harm. Focus on credible news, not studies or opinions."
    ),
    backstory="""
    You are an expert in ethical AI and investigative journalism.
    Your mission is to collect public reports and credible news stories
    detailing AI-related misconduct and failures (e.g., scams, bias, deepfakes, fraud, accidents).
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[get_search_tool(SEARCH_TOOL)],  # ✅ uses hybrid
    allow_delegation=False,
)

# Agent 2: Analyst – validate & enrich each harmful incident
analyst = Agent(
    role="AI Incident Analyst",
    goal=(
        f"Validate and enrich incidents from the Researcher. "
        f"Confirm accuracy using ≥{MIN_SOURCES} credible sources. "
        f"Extract impact, estimated financial loss, and fines (use 'unknown' if missing)."
    ),
    backstory="""
    You are a meticulous fact-checker and analyst.
    You cross-verify incidents using multiple reputable sources
    and ensure accuracy of details about AI harm.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[get_search_tool(SEARCH_TOOL)],  # ✅ uses hybrid
    allow_delegation=False,
)

# Agent 3: Reporter – produce structured JSON
reporter = Agent(
    role="AI Incident Reporter",
    goal="""
    Synthesize the validated incidents into a clear, concise JSON report.
    Each report must include:
    - title
    - summary
    - impact
    - estimated_loss ('unknown' if missing)
    - fine_due_to_non_compliance ('unknown' if missing)
    - sources (list of verified URLs, ≥2)
    """,
    backstory="""
    You are a professional technical writer specializing in structured data journalism.
    You transform verified incident data into JSON for reporting.
    """,
    memory=False,
    verbose=True,
    llm=llm,
    tools=[],  # Reporter doesn’t need search tools
    allow_delegation=False,
)


