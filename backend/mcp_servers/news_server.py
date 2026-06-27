from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP
from langchain.tools import tool
from newsapi import NewsApiClient

from schema.schemas import NewsArticle, NewsToolResponse, SentimentToolResponse

mcp = FastMCP("News")


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized:
        raise ValueError("INVALID_TICKER: ticker cannot be empty")
    return normalized


def _build_article(article: dict[str, Any]) -> NewsArticle:
    published_at = article.get("publishedAt")
    return NewsArticle(
        title=article.get("title"),
        source=article.get("source", {}).get("name") if isinstance(article.get("source"), dict) else None,
        url=article.get("url"),
        published_at=published_at,
        description=article.get("description"),
    )


def _news_client() -> NewsApiClient | None:
    api_key = os.getenv("NEWS_API_KEY") or os.getenv("newsapi_key")
    if not api_key:
        return None
    return NewsApiClient(api_key=api_key)


def _sentiment_from_headlines(articles: list[NewsArticle]) -> tuple[str, float, int, int, int]:
    positive_words = {"gain", "gains", "growth", "up", "surge", "beat", "profit", "strong", "boost"}
    negative_words = {"fall", "drops", "decline", "down", "weak", "loss", "lag", "cut", "warning"}

    positive = 0
    negative = 0
    neutral = 0
    scores: list[float] = []
    for article in articles:
        text = " ".join(filter(None, [article.title, article.description])).lower()
        if not text:
            neutral += 1
            continue
        pos_hits = sum(1 for word in positive_words if word in text)
        neg_hits = sum(1 for word in negative_words if word in text)
        if pos_hits > neg_hits:
            positive += 1
            scores.append(1.0)
        elif neg_hits > pos_hits:
            negative += 1
            scores.append(-1.0)
        else:
            neutral += 1
            scores.append(0.0)

    if not scores:
        return "neutral", 0.0, 0, 0, 0

    average_score = sum(scores) / len(scores)
    if average_score > 0.1:
        label = "positive"
    elif average_score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return label, round(average_score, 3), positive, negative, neutral


@tool
def get_news_tool(ticker: str, days: int = 7) -> NewsToolResponse:
    """Retrieve recent news articles for a given stock ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days: Number of days to look back for news (default 7)
        
    Returns:
        NewsToolResponse containing articles and sentiment analysis
    """
    return _get_news_impl(ticker, days)


@mcp.tool
def get_news(ticker: str, days: int = 7) -> NewsToolResponse:
    """Retrieve recent news articles for a given stock ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days: Number of days to look back for news (default 7)
        
    Returns:
        NewsToolResponse containing articles and sentiment analysis
    """
    return _get_news_impl(ticker, days)


def _get_news_impl(ticker: str, days: int = 7) -> NewsToolResponse:
    normalized_ticker = _normalize_ticker(ticker)
    client = _news_client()
    articles: list[NewsArticle] = []

    if client is None:
        return NewsToolResponse(ticker=normalized_ticker, days=days, articles=articles)

    try:
        response = client.get_everything(
            q=normalized_ticker,
            language="en",
            sort_by="publishedAt",
            page_size=5,
        )
    except Exception:
        return NewsToolResponse(ticker=normalized_ticker, days=days, articles=articles)

    raw_articles = response.get("articles", []) if isinstance(response, dict) else []
    articles = [_build_article(article) for article in raw_articles if isinstance(article, dict)]
    return NewsToolResponse(ticker=normalized_ticker, days=days, articles=articles[:5])


@tool
def get_sentiment_score_tool(ticker: str) -> SentimentToolResponse:
    """Analyze sentiment of recent news articles for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        SentimentToolResponse with overall sentiment label and score
    """
    return _get_sentiment_score_impl(ticker)


@mcp.tool
def get_sentiment_score(ticker: str) -> SentimentToolResponse:
    """Analyze sentiment of recent news articles for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        SentimentToolResponse with overall sentiment label and score
    """
    return _get_sentiment_score_impl(ticker)


def _get_sentiment_score_impl(ticker: str) -> SentimentToolResponse:
    normalized_ticker = _normalize_ticker(ticker)
    news_result = _get_news_impl(normalized_ticker, 7)
    label, score, positive, negative, neutral = _sentiment_from_headlines(news_result.articles)
    return SentimentToolResponse(
        ticker=normalized_ticker,
        label=label,
        score=score,
        positive_headlines=positive,
        negative_headlines=negative,
        neutral_headlines=neutral,
    )


def build_langchain_tools() -> list[Any]:
    return [get_news_tool, get_sentiment_score_tool]


if __name__ == "__main__":
    mcp.run(transport="stdio")
