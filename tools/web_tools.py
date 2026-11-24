from .base_tool import BaseTool
from security.security_manager import SecurityManager


class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Searches the web using DuckDuckGo (with Wikipedia fallback) for up-to-date information, facts, or news."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5)"
                }
            },
            "required": ["query"]
        }

    @property
    def risk_level(self) -> int:
        return SecurityManager.RISK_SAFE

    def execute(self, query: str, max_results: int = 5, **kwargs) -> str:
        errors = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if results:
                formatted = []
                for idx, r in enumerate(results, 1):
                    title = r.get("title", "No title")
                    snippet = r.get("body", r.get("snippet", ""))
                    href = r.get("href", r.get("link", ""))
                    formatted.append(f"{idx}. {title}\n   {snippet}\n   URL: {href}")
                return "Web Search Results:\n" + "\n".join(formatted)
        except Exception as e:
            errors.append(f"DuckDuckGo error: {e}")

        # Fallback to Wikipedia summary if DuckDuckGo fails or returns nothing
        try:
            import wikipedia
            summary = wikipedia.summary(query, sentences=3)
            return f"Wikipedia Summary for '{query}':\n{summary}"
        except Exception as e:
            errors.append(f"Wikipedia error: {e}")

        return f"No web results found for '{query}'. ({'; '.join(errors)})"

