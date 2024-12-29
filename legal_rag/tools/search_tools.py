from typing import List, Dict, Any
from pydantic import BaseModel
from langchain.tools import Tool
from crewai_tools import SerperDevTool

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str

def create_search_tools() -> List[Tool]:
    """Create and return a list of search tools"""
    return [SerperDevTool()]
