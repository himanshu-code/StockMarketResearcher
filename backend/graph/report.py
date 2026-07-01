from __future__ import annotations

import logging
import re
from datetime import date

from openai import OpenAI
import os

from .state import ResearchState

logger=logging.getLogger(__name__)

_signal_map={"bullish": "🟢 Bullish", "neutral": "🟡 Neutral", "bearish": "🔴 Bearish"}

_REPORT_SYSTEM_PROMPT="""\
    You are a senior equity research analyst. Given structured stock research data, write a \
polished Markdown investment report with EXACTLY these six sections in order:
1. ## Executive Summary
2. ## Price Analysis
3. ## News Sentiment
4. ## Fundamentals Snapshot
5. ## Risk Factors
6. ## Signal
Rules:
- In "## Price Analysis" mention the momentum trend (bullish/bearish/neutral).
- In "## News Sentiment" include the sentiment score and up to 3 top headlines.
- In "## Fundamentals Snapshot" include P/E (if available), EPS, revenue, and market cap.
- In "## Risk Factors" list 2–4 concrete risks derived from the data.
- In "## Signal" output EXACTLY one line: `Signal: <🟢 Bullish|🟡 Neutral|🔴 Bearish> — Confidence: <0–100>%`
- After the Signal section add `## Sources` listing the data sources.
- Do not add any section outside the six above.
- Write in a professional but concise tone.
    """

def _call_llm(prompt:str)->str:
    """call OpenAi directly (outside crewAI) for report synthesis"""
    client=OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    response=client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role":"system","content":_REPORT_SYSTEM_PROMPT},
            {"role":"user","content":prompt}
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""

def _extract_signal(report_md:str)->tuple[str,float]:
    """Parse 'Signal: 🟢 Bullish — Confidence: 87%' from the report."""

    pattern = r"Signal:\s*(🟢\s*Bullish|🟡\s*Neutral|🔴\s*Bearish)\s*[—-]\s*Confidence:\s*(\d+)%"
    match = re.search(pattern, report_md, re.IGNORECASE)
    if match:
        raw_signal = match.group(1).strip()
        confidence = int(match.group(2)) / 100.0
        # Normalise to plain word
        for key in ("Bullish", "Neutral", "Bearish"):
            if key.lower() in raw_signal.lower():
                return key, confidence
    logger.warning("[report_node] Could not extract signal — defaulting to Neutral/0.5")
    return "Neutral", 0.5


def report_node(state:ResearchState)->dict:
    """Synthesis all research state fields into a polished Markdown report via llm"""
    ticker=state["ticker"]
    md=state.get("market_data",{})
    ns=state.get("news_sentiment",{})
    fu=state.get("fundamentals",{})
    critique=state.get("critique","No critique available")

    user_prompt=f"""
    Ticker: {ticker}
    Report Date: {date.today().isoformat()}
    --- MARKET DATA ---
    {md}
    --- NEWS SENTIMENT ---
    {ns}
    --- FUNDAMENTALS ---
    {fu}
    --- CRITIC REVIEW ---
    {critique}
    Write the full Markdown report now.
    """ 
    try:
        report_md=_call_llm(user_prompt)
        title = f"# {ticker} Research Report — {date.today().isoformat()}\n\n"
        full_report = title + report_md
    except Exception:
        logger.exception("[Report_NODE] LLM failed for %s - falling back to template",ticker)
        full_report=_fallback_report(ticker,md,ns,fu,critique)
    signal,confidence=_extract_signal(full_report)
    return {
        "report": full_report,
        "signal": signal,
        "confidence": confidence,
        "status": "complete",
    }

def _fallback_report(ticker: str, md: dict, ns: dict, fu: dict, critique: str) -> str:
    """Minimal template-based fallback if the LLM call fails."""
    top_headlines = ns.get("top_headlines") or []
    headlines_md = "\n".join(f"  - {h}" for h in top_headlines) or "  - N/A"
    return f"""# {ticker} Research Report — {date.today().isoformat()}
## Executive Summary
Research completed for {ticker}. Data quality: {critique}
## Price Analysis
- Current Price: {md.get("current_price", "N/A")} {md.get("currency", "")}
- Day Change: {md.get("percentage_change", "N/A")}%
- Trend: {md.get("trend", "N/A")}
- 52-Week High: {md.get("high_52w", "N/A")} | Low: {md.get("low_52w", "N/A")}
## News Sentiment
- Overall: {ns.get("label", "N/A")} (score: {ns.get("score", "N/A")})
- Positive / Negative / Neutral: {ns.get("positive_headlines", 0)} / {ns.get("negative_headlines", 0)} / {ns.get("neutral_headlines", 0)}
- Top Headlines:
{headlines_md}
## Fundamentals Snapshot
- Company: {fu.get("company_name", "N/A")} | Sector: {fu.get("sector", "N/A")}
- Market Cap: {fu.get("market_cap", "N/A")} | Revenue: {fu.get("revenue", "N/A")}
- Net Income: {fu.get("net_income", "N/A")} | Fiscal Year: {fu.get("fiscal_year", "N/A")}
## Risk Factors
- Data may be incomplete; verify before making investment decisions.
## Signal
Signal: 🟡 Neutral — Confidence: 50%
## Sources
- Yahoo Finance, NewsAPI
"""
    