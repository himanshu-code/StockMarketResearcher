from __future__ import annotations

import logging
import re
from datetime import date

from typing import Any
from langfuse.openai import OpenAI
from observability.langfuse_client import get_langfuse_client
import os

from .state import ResearchState
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

GoogleGenAIInstrumentor().instrument()

logger=logging.getLogger(__name__)

_signal_map={"bullish": "🟢 Bullish", "neutral": "🟡 Neutral", "bearish": "🔴 Bearish"}

# System prompt migrated to Langfuse Prompt Registry ('report-system-prompt')

def _call_llm(prompt:str, system_prompt: str, prompt_obj: Any = None, trace_id: str | None = None)->str:
    """call OpenAI or Gemini for report synthesis based on LLM_PROVIDER"""
    from config.settings import get_settings
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    
    if provider == "gemini":
        from google import genai
        from google.genai import types
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        # Manually create a generation observation to link prompt and trace
        generation = None
        if prompt_obj:
            lf = get_langfuse_client()
            generation = lf.generation(
                name="report-synthesis-gemini",
                model="gemini-2.5-flash",
                input={"user_prompt": prompt, "system_instruction": system_prompt},
                prompt=prompt_obj,
                trace_context={"trace_id": trace_id} if trace_id else None,
            )
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
        )
        
        if generation:
            generation.update(output=response.text or "")
            generation.end()
            
        return response.text or ""
    elif provider == "mistral":
        client = OpenAI(
            base_url="https://api.mistral.ai/v1",
            api_key=settings.mistral_api_key or os.getenv("MISTRAL_API_KEY")
        )
        response = client.chat.completions.create(
            model="ministral-3b-2512",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            langfuse_prompt=prompt_obj
        )
        return response.choices[0].message.content or ""
    else:
        client=OpenAI(
            base_url=settings.base_url or os.getenv("OPENAI_BASE_URL"),
            api_key=settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        response=client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":prompt}
            ],
            temperature=0.2,
            langfuse_prompt=prompt_obj
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


def report_node(state:ResearchState, config: dict = None)->dict:
    """Synthesis all research state fields into a polished Markdown report via llm"""
    ticker=state["ticker"]
    md=state.get("market_data",{})
    ns=state.get("news_sentiment",{})
    fu=state.get("fundamentals",{})
    critique=state.get("critique","No critique available")
    rag_context=state.get("rag_context",[])

    trace_id = (config or {}).get("metadata", {}).get("langfuse_trace_id")
    lf = get_langfuse_client()
    
    # 1. Fetch system prompt from Langfuse (with fallback for case mismatch)
    try:
        prompt_obj = lf.get_prompt("report-system-prompt", label="production")
    except Exception:
        try:
            prompt_obj = lf.get_prompt("Report-system-prompt", label="production")
        except Exception as exc:
            logger.error("Failed to fetch report-system-prompt or Report-system-prompt from Langfuse: %s", exc)
            raise
    system_prompt = prompt_obj.compile()

    span = lf.start_observation(
        as_type="span",
        trace_context={"trace_id": trace_id} if trace_id else None,
        name=f"report/{ticker}",
        input={"ticker": ticker},
        metadata={"node": "report"},
    )

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
        report_md = _call_llm(user_prompt, system_prompt, prompt_obj, trace_id)
        
        # Clean any wrapping markdown code blocks from the LLM response
        report_md = report_md.strip()
        if report_md.startswith("```markdown"):
            report_md = report_md[11:]
        elif report_md.startswith("```"):
            report_md = report_md[3:]
        if report_md.endswith("```"):
            report_md = report_md[:-3]
        report_md = report_md.strip()

        title = f"# {ticker} Research Report — {date.today().isoformat()}\n\n"
        full_report = title + report_md
        error_occurred = False
    except Exception:
        logger.exception("[Report_NODE] LLM failed for %s - falling back to template",ticker)
        full_report=_fallback_report(ticker,md,ns,fu,critique)
        error_occurred = True
    signal,confidence=_extract_signal(full_report)

    rag_context_text = "\n\n---\n\n".join(rag_context) if rag_context else ""
    eval_output = {
        "signal": signal,
        "confidence": confidence,
        "report": full_report,
        "rag_context": rag_context_text,
    }
    if error_occurred:
        span.update(level="ERROR", output=eval_output)
    else:
        span.update(output=eval_output)
    span.end()

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
    