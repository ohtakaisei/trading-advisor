"""Phase B: LLM agent that performs deep analysis on Phase A survivors."""

import json
import re
import logging
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import LLM_MODEL, LLM_TEMPERATURE, AGENT_MAX_ITERATIONS
from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT, format_analysis_prompt
from screener import run_screener

load_dotenv()
logger = logging.getLogger(__name__)


def create_agent_graph():
    """Create the LangGraph react agent with tools."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    graph = create_react_agent(
        llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )

    return graph


def extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON from LLM response using 3 strategies."""
    if not text or not text.strip():
        return None

    text = text.strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Code block extraction
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: Brace matching
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    return None


def _empty_report(screening_results: dict, error: str) -> dict:
    """Return a minimal report when LLM fails."""
    return {
        "market_overview": {
            "trend": "unknown",
            "spy_change_5d": None,
            "vix": None,
            "vix_level": "unknown",
            "treasury_10y": None,
            "sector_leaders": [],
            "sector_laggards": [],
            "summary": f"Analysis incomplete: {error}",
        },
        "candidates": [],
        "watchlist": [
            {
                "ticker": s["ticker"],
                "trigger_condition": ", ".join(s.get("signals", [])),
                "direction": s.get("direction", "neutral"),
                "notes": "From Phase A screening (LLM analysis unavailable)",
            }
            for s in screening_results.get("passed", [])[:5]
        ],
        "risk_warnings": [f"Automated analysis failed: {error}. Data shown is from rule-based screening only."],
        "screening_stats": {
            "total_universe": screening_results.get("total_universe", 0),
            "phase_a_passed": screening_results.get("passed_count", 0),
            "phase_b_candidates": 0,
            "watchlist_count": min(len(screening_results.get("passed", [])), 5),
        },
    }


def run_analysis() -> dict:
    """Execute the full analysis pipeline: Phase A screening -> Phase B LLM agent."""
    logger.info("Starting Phase A: Rule-based screening")
    screening_results = run_screener()
    logger.info(
        f"Phase A complete: {screening_results['passed_count']}/{screening_results['total_universe']} passed"
    )

    # Format prompt for LLM
    analysis_prompt = format_analysis_prompt(screening_results)

    # Create and run agent
    logger.info("Starting Phase B: LLM deep analysis")
    graph = create_agent_graph()

    max_retries = 2
    report = None

    for attempt in range(max_retries):
        try:
            result = graph.invoke(
                {"messages": [{"role": "user", "content": analysis_prompt}]},
                config={"recursion_limit": AGENT_MAX_ITERATIONS * 2},
            )

            # Extract the final AI message content
            messages = result.get("messages", [])
            output_text = ""
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                    output_text = msg.content
                    break

            logger.info(f"Agent output (attempt {attempt + 1}): {output_text[:200]}...")

            report = extract_json_from_response(output_text)
            if report is not None:
                break

            logger.warning(f"JSON extraction failed on attempt {attempt + 1}")

        except Exception as e:
            logger.error(f"Agent execution failed on attempt {attempt + 1}: {e}")

    if report is None:
        logger.error("All attempts to get valid JSON from LLM failed")
        report = _empty_report(screening_results, "LLM failed to produce valid JSON")

    # Inject accurate Phase A stats (LLM may hallucinate numbers)
    if "screening_stats" not in report:
        report["screening_stats"] = {}
    report["screening_stats"]["total_universe"] = screening_results["total_universe"]
    report["screening_stats"]["phase_a_passed"] = screening_results["passed_count"]
    report["screening_stats"]["phase_b_candidates"] = len(report.get("candidates", []))
    report["screening_stats"]["watchlist_count"] = len(report.get("watchlist", []))

    # Ensure required keys exist
    report.setdefault("market_overview", {})
    report.setdefault("candidates", [])
    report.setdefault("watchlist", [])
    report.setdefault("risk_warnings", [])

    return report
