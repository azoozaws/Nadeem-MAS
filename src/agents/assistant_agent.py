import os
import datetime
from langgraph.graph import StateGraph, START, END


class AssistantAgent:
    """>>>"""
    def __init__(self):
        self.graph = self._build_graph()


    def _build_graph(self):
        graph = StateGraph()

        # -- Nodes --
        graph.add_node("greet_user", self._greet_user)
        graph.add_node("extract_data", self._extract_data)
        graph.add_node("researcher", self._researcher)
        graph.add_node("manager", self._manager)
        graph.add_node("updater", self._updater)
        graph.add_node("summarizer", self._summarizer)

        # -- Edges --
        graph.add_edge(START, "greet_user")
        graph.add_edge("greet_user", "extract_data")
        graph.add_edge("extract_data", "researcher")
        graph.add_edge("researcher", "manager")
        graph.add_edge("manager", "updater")
        graph.add_edge("updater", "summarizer")
        graph.add_edge("summarizer", END)

        return graph.compile()

    def run(self):
        raise NotImplementedError