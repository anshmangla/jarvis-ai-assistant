import requests
from typing import Any, Dict

from skills.base import BaseSkill
from utils.logger import logger

class WebSearchSkill(BaseSkill):
    """Skill to search the web using DuckDuckGo HTML parsing (or API fallback) and summarize."""
    
    name = "web_search"
    description = "Search the web for real-time information and latest news."
    parameters = {
        "query": {
            "type": "string",
            "description": "The search query to look up on the web."
        }
    }

    def run(self, **kwargs: Dict[str, Any]) -> str:
        query = kwargs.get("query", "")
        if not query:
            return "No search query provided."
            
        logger.info(f"Initiating web search for: '{query}'")
        
        try:
            # We use the DuckDuckGo Lite HTML interface for simple public scraping
            # Using the api.duckduckgo.com often doesn't give full web results (it's mainly for instant answers)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Simple summarization: parse the snippets using BeautifulSoup if available, 
            # else quick string manipulation
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                for result in soup.find_all('a', class_='result__snippet')[:3]:
                    results.append(result.text.strip())
                    
                if not results:
                    return f"No useful snippets found for query: '{query}'"
                
                summary = "Top search results:\n" + "\n".join([f"- {res}" for res in results])
                return summary
            except ImportError:
                return "The web search was successful, but 'beautifulsoup4' is required to parse the results format. Please install it."
                
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            return f"Failed to perform web search. Error: {e}"
