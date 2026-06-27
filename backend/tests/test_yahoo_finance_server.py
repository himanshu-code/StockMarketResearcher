import unittest
from unittest.mock import patch

import pandas as pd

from mcp_servers.yahoo_finance_server import _get_financials


class FakeTicker:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker

    def get_income_stmt(self, freq: str) -> pd.DataFrame:
        self._assert_yearly(freq)
        return pd.DataFrame(
            {
                pd.Timestamp("2024-12-31"): [
                    1000.0,
                    600.0,
                    250.0,
                    180.0,
                    4.25,
                ],
                pd.Timestamp("2025-12-31"): [
                    1200.0,
                    720.0,
                    300.0,
                    220.0,
                    5.10,
                ],
            },
            index=[
                "Total Revenue",
                "Gross Profit",
                "Operating Income",
                "Net Income",
                "Diluted EPS",
            ],
        )

    def get_balance_sheet(self, freq: str) -> pd.DataFrame:
        self._assert_yearly(freq)
        return pd.DataFrame(
            {
                pd.Timestamp("2025-12-31"): [
                    3000.0,
                    1800.0,
                    1200.0,
                    500.0,
                    700.0,
                ]
            },
            index=[
                "Total Assets",
                "Total Liabilities Net Minority Interest",
                "Stockholders Equity",
                "Cash Cash Equivalents And Short Term Investments",
                "Total Debt",
            ],
        )

    def get_info(self) -> dict:
        return {"financialCurrency": "USD"}

    @staticmethod
    def _assert_yearly(freq: str) -> None:
        if freq != "yearly":
            raise AssertionError("Expected yearly financial statements")


class EmptyTicker(FakeTicker):
    def get_income_stmt(self, freq: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_balance_sheet(self, freq: str) -> pd.DataFrame:
        return pd.DataFrame()


class YahooFinanceFinancialsTests(unittest.TestCase):
    @patch("mcp_servers.yahoo_finance_server.Ticker", FakeTicker)
    def test_get_financials_uses_latest_reporting_year(self) -> None:
        result = _get_financials(" aapl ")

        self.assertEqual(result.ticker, "AAPL")
        self.assertEqual(result.currency, "USD")
        self.assertEqual(result.fiscal_year, 2025)
        self.assertEqual(result.income_statement.total_revenue, 1200.0)
        self.assertEqual(result.income_statement.diluted_eps, 5.10)
        self.assertEqual(result.balance_sheet.total_assets, 3000.0)
        self.assertEqual(result.balance_sheet.total_debt, 700.0)

    def test_get_financials_rejects_empty_ticker(self) -> None:
        with self.assertRaisesRegex(ValueError, "INVALID_TICKER"):
            _get_financials(" ")

    @patch("mcp_servers.yahoo_finance_server.Ticker", EmptyTicker)
    def test_get_financials_rejects_empty_statements(self) -> None:
        with self.assertRaisesRegex(ValueError, "DATA_NOT_FOUND"):
            _get_financials("AAPL")


if __name__ == "__main__":
    unittest.main()
