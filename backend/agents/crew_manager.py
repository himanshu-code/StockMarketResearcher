from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from crewai import Crew, Process, Task

from .FundamentalsAgent import fundamentalsAgent
from .MarketDataAgent import marketDataAgent
from .NewsSentimentAgent import newsSentimentAgent


@dataclass
class ResearchOutput:
    ticker: str
    market_data: dict[str, Any]
    news_sentiment: dict[str, Any]
    fundamentals: dict[str, Any]


def _parse_json_output(raw_output: str) -> dict[str, Any] | None:
    if raw_output is None:
        return None

    text = raw_output.strip()
    if "```json" in text:
        try:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            logging.warning("Unable to split JSON code block from task output")
    elif "```" in text:
        try:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            logging.warning("Unable to split code block from task output")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logging.warning("Failed to parse crew task output as JSON: %s", exc)
        return None


def _build_tasks() -> tuple[Task, Task, Task]:
    """Construct the three research tasks. Tasks are created fresh each call
    so that previous run outputs do not pollute subsequent runs."""

    market_data_task = Task(
        name="market_data",
        description=(
            "Retrieve the current stock price for {ticker} using get_stock_price. "
            "Then retrieve recent price history using get_ohlcv with period='5d' — "
            "call get_ohlcv ONCE with period='5d' only (do NOT call it again with any other period). "
            "Using the price data, identify whether the stock is in an uptrend, downtrend, or neutral. "
            "Return ONLY a single valid JSON object (no markdown, no extra text) with these exact keys: "
            "current_price (float), percentage_change (float), currency (str), "
            "trend (str — one of 'bullish', 'bearish', or 'neutral'), "
            "high_52w (null), low_52w (null), source (str set to 'yahoo_finance')."
        ),
        expected_output=(
            "A single JSON object with keys: current_price, percentage_change, currency, "
            "trend, high_52w, low_52w, source."
        ),
        agent=marketDataAgent,
    )

    news_sentiment_task = Task(
        name="news_sentiment",
        description=(
            "Retrieve the latest 7 days of news articles for {ticker} and compute "
            "an overall sentiment score. Classify each headline as positive, negative, "
            "or neutral. "
            "Return ONLY a valid JSON object with the following keys: "
            "label (str: 'positive' | 'negative' | 'neutral'), score (float between -1 and 1), "
            "positive_headlines (int), negative_headlines (int), neutral_headlines (int), "
            "top_headlines (list of str, max 3), source (str)."
        ),
        expected_output=(
            "A JSON object with keys: label, score, positive_headlines, "
            "negative_headlines, neutral_headlines, top_headlines, source."
        ),
        agent=newsSentimentAgent,
        context=[market_data_task],
    )

    fundamentals_task = Task(
        name="fundamentals",
        description=(
            "Retrieve company profile and the most recent annual financial statements "
            "for {ticker}. Summarise the key financial health indicators. "
            "Return ONLY a valid JSON object with the following keys: "
            "company_name (str), sector (str), industry (str), market_cap (float or null), "
            "revenue (float or null), net_income (float or null), "
            "total_assets (float or null), total_liabilities (float or null), "
            "total_equity (float or null), currency (str or null), "
            "fiscal_year (int or null), source (str)."
        ),
        expected_output=(
            "A JSON object with keys: company_name, sector, industry, market_cap, "
            "revenue, net_income, total_assets, total_liabilities, total_equity, "
            "currency, fiscal_year, source."
        ),
        agent=fundamentalsAgent,
        context=[market_data_task],
    )

    return market_data_task, news_sentiment_task, fundamentals_task


class ResearchCrew:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def run_research(self, ticker: str) -> ResearchOutput:
        ticker = ticker.upper()

        # Build fresh tasks every run so output state doesn't leak.
        market_data_task, news_sentiment_task, fundamentals_task = _build_tasks()

        crew = Crew(
            agents=[marketDataAgent, newsSentimentAgent, fundamentalsAgent],
            tasks=[market_data_task, news_sentiment_task, fundamentals_task],
            process=Process.sequential,
            verbose=self.verbose,
            memory=False,
        )

        try:
            crew.kickoff(inputs={"ticker": ticker})
        except Exception as exc:
            logging.error("ResearchCrew execution failed for %s: %s", ticker, exc)
            return self._default_output(ticker)

        market_data = self._parse_task_output(market_data_task)
        news_sentiment = self._parse_task_output(news_sentiment_task)
        fundamentals = self._parse_task_output(fundamentals_task)

        return ResearchOutput(
            ticker=ticker,
            market_data=market_data,
            news_sentiment=news_sentiment,
            fundamentals=fundamentals,
        )

    def _parse_task_output(self, task: Task) -> dict[str, Any]:
        if task.output is None:
            return self._default_suboutput(task.name or "")

        parsed = _parse_json_output(task.output.raw or "")
        if parsed is None:
            return self._default_suboutput(task.name or "")

        return parsed

    def _default_suboutput(self, task_name: str) -> dict[str, Any]:
        defaults: dict[str, dict[str, Any]] = {
            "market_data": {
                "current_price": 0.0,
                "percentage_change": 0.0,
                "currency": "USD",
                "trend": "neutral",
                "high_52w": None,
                "low_52w": None,
                "source": "error",
            },
            "news_sentiment": {
                "label": "neutral",
                "score": 0.0,
                "positive_headlines": 0,
                "negative_headlines": 0,
                "neutral_headlines": 0,
                "top_headlines": [],
                "source": "error",
            },
            "fundamentals": {
                "company_name": None,
                "sector": None,
                "industry": None,
                "market_cap": None,
                "revenue": None,
                "net_income": None,
                "total_assets": None,
                "total_liabilities": None,
                "total_equity": None,
                "currency": None,
                "fiscal_year": None,
                "source": "error",
            },
        }
        return defaults.get(task_name, {})

    def _default_output(self, ticker: str) -> ResearchOutput:
        return ResearchOutput(
            ticker=ticker,
            market_data=self._default_suboutput("market_data"),
            news_sentiment=self._default_suboutput("news_sentiment"),
            fundamentals=self._default_suboutput("fundamentals"),
        )


_crew_instance: ResearchCrew | None = None


def get_research_crew(verbose: bool = False) -> ResearchCrew:
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = ResearchCrew(verbose=verbose)
    return _crew_instance

