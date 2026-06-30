import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from schema.schemas import (
    BalanceSheetSummary,
    FinancialsToolResponse,
    IncomeStatementSummary,
    NewsArticle,
    NewsToolResponse,
    SentimentToolResponse,
    StockPriceToolResponse,
)


class ToolSchemaTests(unittest.TestCase):
    def test_financials_response_accepts_numeric_summaries(self) -> None:
        response = FinancialsToolResponse(
            ticker="AAPL",
            currency="USD",
            fiscal_year=2025,
            income_statement=IncomeStatementSummary(
                total_revenue=416_161_000_000.0,
                gross_profit=195_201_000_000.0,
                operating_income=133_050_000_000.0,
                net_income=112_010_000_000.0,
                diluted_eps=7.15,
            ),
            balance_sheet=BalanceSheetSummary(
                total_assets=359_241_000_000.0,
                total_liabilities=285_508_000_000.0,
                total_equity=73_733_000_000.0,
                cash_and_cash_equivalents=35_934_000_000.0,
                total_debt=98_657_000_000.0,
            ),
        )

        self.assertIsInstance(response.income_statement.total_revenue, float)
        self.assertIsInstance(response.balance_sheet.total_assets, float)
        self.assertEqual(response.fiscal_year, 2025)

    def test_financials_response_allows_unavailable_provider_fields(self) -> None:
        response = FinancialsToolResponse(
            ticker="PRIVATE",
            income_statement=IncomeStatementSummary(),
            balance_sheet=BalanceSheetSummary(total_debt=None),
        )

        self.assertIsNone(response.currency)
        self.assertIsNone(response.fiscal_year)
        self.assertIsNone(response.income_statement.net_income)
        self.assertIsNone(response.balance_sheet.total_debt)

    def test_news_response_accepts_articles_and_parses_timestamp(self) -> None:
        response = NewsToolResponse(
            ticker="TSLA",
            days=7,
            articles=[
                NewsArticle(
                    title="Tesla announces an update",
                    source="Example News",
                    url="https://example.com/tesla-update",
                    published_at="2026-06-25T10:30:00Z",
                )
            ],
        )

        self.assertEqual(len(response.articles), 1)
        self.assertEqual(
            response.articles[0].published_at,
            datetime(2026, 6, 25, 10, 30, tzinfo=timezone.utc),
        )

    def test_news_article_allows_unavailable_provider_fields(self) -> None:
        response = NewsToolResponse(
            ticker="TSLA",
            days=7,
            articles=[NewsArticle(title="Headline only")],
        )

        article = response.articles[0]
        self.assertIsNone(article.source)
        self.assertIsNone(article.url)
        self.assertIsNone(article.published_at)
        self.assertIsNone(article.description)

    def test_sentiment_response_accepts_valid_values(self) -> None:
        response = SentimentToolResponse(
            ticker="TSLA",
            label="positive",
            score=0.75,
            positive_headlines=3,
            negative_headlines=1,
            neutral_headlines=0,
        )

        self.assertIsInstance(response.score, float)
        self.assertEqual(response.positive_headlines, 3)

    def test_invalid_numeric_values_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            IncomeStatementSummary(total_revenue="not-a-number")

        with self.assertRaises(ValidationError):
            StockPriceToolResponse(
                current_price="unknown",
                percentage_change=1.5,
            )

    def test_invalid_news_and_sentiment_types_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            NewsToolResponse(ticker="TSLA", days="last week")

        with self.assertRaises(ValidationError):
            SentimentToolResponse(
                ticker="TSLA",
                label="bullish",
                score=0.5,
            )


if __name__ == "__main__":
    unittest.main()
