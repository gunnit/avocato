from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
from pydantic import BaseModel
from crewai_tools import SerperDevTool
import os

class SearchResult(BaseModel):
    """Model for search results that accepts any dictionary structure"""
    result: Dict[str, Any]  # Accepts the entire crew AI output as a dictionary

class LegalSearchCrew:

    """A simplified crew for searching legal resources"""

    def researcher(self) -> Agent:
        serper_tool = SerperDevTool()
        # Configure the tool for Italian results
        serper_tool.country = "it"  # Set country to Italy
        serper_tool.locale = "it"   # Set locale to Italian
        serper_tool.n_results = 20  # Increase number of results
        
        return Agent(
            role="Legal Researcher",
            goal="Search and analyze legal resources effectively",
            backstory="""You are an expert in Italian law with deep experience in 
            legal research. You excel at finding relevant legal information and cases.""",
            verbose=True,
            allow_delegation=False,
            tools=[serper_tool]
        )

    def _construct_search_query(self, title: str, description: str) -> str:
        """Construct an effective search query from the case details"""
        # Extract key legal terms from title and description
        key_terms = []
        
        # Extract legal terms from title
        if title:
            # Split title into words and take first 3-4 meaningful terms
            words = title.lower().split()
            legal_terms = ['omicidio', 'frode', 'fiscale', 'violenza', 'reato', 'penale']
            key_terms.extend([word for word in words[:4] if any(term in word for term in legal_terms)])
        
        # If we don't have enough terms from title, look in description
        if len(key_terms) < 2 and description:
            words = description.lower().split()
            legal_terms = ['omicidio', 'frode', 'fiscale', 'violenza', 'reato', 'penale']
            key_terms.extend([word for word in words[:10] if any(term in word for term in legal_terms)][:2])
        
        # Add site restriction
        site_restriction = "site:giurisprudenzapenale.com"
        
        # Combine terms and site restriction
        query = f"{' '.join(key_terms)} {site_restriction}"
        print(f"Constructed search query: {query}")
        return query

    def search_task(self) -> Task:
        return Task(
            description="""Search for legal information related to the following case:
            
            Title: {title}
            Description: {description}
            Search Query: {search_query}
            
            Use the exact search query provided to search for relevant legal information.
            The search query already includes site restriction and key terms.
            
            Execute the search and format your response as a JSON object with this structure:
            {{
                "query": "the exact search query you used",
                "results": [
                    {{
                        "title": "title of result",
                        "url": "url of result",
                        "snippet": "relevant excerpt"
                    }}
                ],
                "source": "giurisprudenzapenale.com"
            }}
            
            Important: Use the exact search query provided without modification to ensure
            results are from giurisprudenzapenale.com.
            """,
            expected_output="""A JSON object containing the search query used, results found,
            and source website.""",
            agent=self.researcher(),
            output_json=SearchResult
        )

    def _parse_serper_results(self, raw_results: str, query: str) -> Dict[str, Any]:
        """Parse the raw results from SerperDevTool into our expected format"""
        try:
            print(f"Raw results to parse: {raw_results}")
            
            # If raw_results is already a dictionary with results
            if isinstance(raw_results, dict):
                print("Results already in dictionary format")
                return {
                    'query': query,
                    'results': raw_results.get('organic', []),
                    'source': 'giurisprudenzapenale.com'
                }
            
            # If raw_results is a string in JSON format
            if isinstance(raw_results, str) and raw_results.strip().startswith('{'):
                try:
                    import json
                    parsed = json.loads(raw_results)
                    if isinstance(parsed, dict):
                        print("Successfully parsed JSON string")
                        return {
                            'query': query,
                            'results': parsed.get('organic', []),
                            'source': 'giurisprudenzapenale.com'
                        }
                except json.JSONDecodeError:
                    print("Failed to parse as JSON, trying line format")
            
            # Fall back to parsing line format
            lines = raw_results.strip().split('\n')
            current_result = {}
            results = []
            
            for line in lines:
                if line.startswith('Title: '):
                    if current_result:
                        results.append(current_result.copy())
                    current_result = {'title': line[7:]}
                elif line.startswith('Link: '):
                    current_result['url'] = line[6:]
                elif line.startswith('Snippet: '):
                    current_result['snippet'] = line[9:]
            
            # Add the last result if it exists
            if current_result:
                results.append(current_result)
            
            print(f"Parsed {len(results)} results")
            for result in results:
                print(f"Result: {result}")
            
            return {
                'query': query,
                'results': results,
                'source': 'giurisprudenzapenale.com'
            }
        except Exception as e:
            print(f"Error parsing results: {e}")
            print(f"Raw results that caused error: {raw_results}")
            return {
                'query': query,
                'results': [],
                'source': 'giurisprudenzapenale.com'
            }

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
            Dictionary containing search results in the format:
            {
                "results_by_source": {
                    "source_name": [
                        {
                            "title": "result title",
                            "url": "result url",
                            "snippet": "result snippet"
                        }
                    ]
                }
            }
        """
        print("Starting legal search with case details:", case_details)
        
        # Construct search query
        query = self._construct_search_query(
            case_details.get("title", ""),
            case_details.get("description", "")
        )
        
        # Prepare search input
        search_input = {
            "title": case_details.get("title", ""),
            "description": case_details.get("description", ""),
            "search_query": query
        }
        
        print(f"Executing search with query: {query}")
        
        # Execute the crew and get results
        result = self.crew().kickoff(inputs=search_input)
        
        print(f"Raw crew result type: {type(result)}")
        print(f"Raw crew result attributes: {dir(result)}")
        print(f"Raw crew result content: {result}")
        
        # Parse the results
        parsed_results = {}
        if hasattr(result, 'json_dict'):
            print("Using JSON dict results")
            parsed_results = result.json_dict.get('result', {})
            print(f"JSON dict results: {parsed_results}")
        elif hasattr(result, 'raw'):
            print("Parsing raw results")
            parsed_results = self._parse_serper_results(result.raw, query)
            print(f"Parsed results: {parsed_results}")
        else:
            print("No valid results found, using empty results")
            parsed_results = {
                'query': query,
                'results': [],
                'source': 'giurisprudenzapenale.com'
            }
        
        # Format results for database
        formatted_results = {
            "results_by_source": {
                parsed_results.get('source', 'giurisprudenzapenale.com'): [
                    {
                        "title": r.get('title', ''),
                        "url": r.get('url', ''),
                        "snippet": r.get('snippet', '')
                    }
                    for r in parsed_results.get('results', [])
                ]
            }
        }
        
        print(f"Formatted results for database: {formatted_results}")
        print(f"Number of results found: {len(formatted_results['results_by_source'].get('giurisprudenzapenale.com', []))}")
        return formatted_results
