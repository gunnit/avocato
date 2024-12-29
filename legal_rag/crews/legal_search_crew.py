from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
from pydantic import BaseModel
from crewai_tools import SerperDevTool
import os

class SearchResult(BaseModel):
    """Model for structured search results"""
    query: str
    results: list[Dict[str, str]]
    source: str

class LegalSearchCrew:
    """A simplified crew for searching legal resources"""

    def researcher(self) -> Agent:
        return Agent(
            role="Legal Researcher",
            goal="Search and analyze legal resources effectively",
            backstory="""You are an expert in Italian law with deep experience in 
            legal research. You excel at finding relevant legal information and cases.""",
            verbose=True,
            allow_delegation=False,
            tools=[SerperDevTool()]
        )

    def search_task(self) -> Task:
        return Task(
            description="""Search for legal information related to the following case:
            
            Title: {title}
            Description: {description}
            
            Focus on finding relevant legal precedents, laws, and interpretations.
            Search specifically on giurisprudenzapenale.com and related legal websites.
            
            Format your response as a JSON object with this structure:
            {{
                "query": "the search query you used",
                "results": [
                    {{
                        "title": "title of result",
                        "url": "url of result",
                        "snippet": "relevant excerpt"
                    }}
                ],
                "source": "name of website"
            }}
            """,
            expected_output="""A JSON object containing the search query used, results found,
            and source website.""",
            agent=self.researcher(),
            output_json=SearchResult
        )

    def crew(self) -> Crew:
        return Crew(
            agents=[self.researcher()],
            tasks=[self.search_task()],
            process=Process.sequential,
            verbose=True
        )

    def kickoff(self, case_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the crew's search process with the provided case details
        
        Args:
            case_details: Dictionary containing case information including:
                - title: Case title
                - description: Case description
                
        Returns:
            Dictionary containing search results
        """
        search_input = {
            "title": case_details.get("title", ""),
            "description": case_details.get("description", "")
        }
        
        # Execute the crew and get results
        result = self.crew().kickoff(inputs=search_input)
        
        # Access the JSON output
        if result.json_dict:
            return result.json_dict
        
        # Fallback to raw output if JSON parsing fails
        return {"error": "Failed to parse results", "raw_output": result.raw}
