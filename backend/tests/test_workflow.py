import unittest

from graph.workflow import (
    MAX_ITERATIONS,
    graph,
    researcher_node,
    route_after_critique,
)


def initial_state(ticker: str = "AAPL") -> dict:
    return {
        "ticker": ticker,
        "market_data": {},
        "news_sentiment": {},
        "fundamentals": {},
        "critique": "",
        "report": "",
        "iteration": 0,
        "status": "pending",
    }


class ResearchWorkflowTests(unittest.TestCase):
    def test_graph_returns_a_report_for_aapl(self) -> None:
        result = graph.invoke(initial_state())

        self.assertEqual(result["ticker"], "AAPL")
        self.assertTrue(result["report"])
        self.assertEqual(result["iteration"], 1)
        self.assertEqual(result["status"], "complete")

    def test_unapproved_research_retries_below_limit(self) -> None:
        state = initial_state()
        state.update({"critique": "needs more evidence", "iteration": 1})

        self.assertEqual(route_after_critique(state), "retry")

    def test_researcher_increments_iteration_on_retry(self) -> None:
        state = initial_state()
        first_result = researcher_node(state)
        state.update(first_result)
        second_result = researcher_node(state)

        self.assertEqual(first_result["iteration"], 1)
        self.assertEqual(second_result["iteration"], 2)

    def test_graph_stops_retrying_at_iteration_limit(self) -> None:
        state = initial_state()
        state.update(
            {
                "critique": "needs more evidence",
                "iteration": MAX_ITERATIONS,
            }
        )

        self.assertEqual(route_after_critique(state), "report")


if __name__ == "__main__":
    unittest.main()
