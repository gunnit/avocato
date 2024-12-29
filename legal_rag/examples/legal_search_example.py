from legal_rag.crews.legal_search_crew import LegalSearchCrew
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def run_legal_search_example():
    """Example usage of the Legal Search Crew"""
    
    # Example case details
    case_details = {
        "description": """
        Case involves allegations of unauthorized access to computer systems 
        and subsequent data theft. The defendant is accused of accessing 
        corporate databases without permission and extracting sensitive 
        customer information.
        """,
        "key_elements": [
            "unauthorized computer access",
            "data theft",
            "corporate database intrusion"
        ],
        "jurisdiction": "Italy",
        "date_of_incident": "2023-12-15"
    }
    
    # Initialize the crew
    crew = LegalSearchCrew()
    
    # Start the search process
    try:
        print("\nStarting legal research process...")
        results = crew.kickoff(case_details)
        
        # Print results in a structured format
        print("\nSearch Results:")
        print("=" * 80)
        
        if isinstance(results, str):
            results = json.loads(results)
        
        # Print search strategy
        if "search_strategy" in results:
            print("\nSearch Strategy Used:")
            print("-" * 40)
            print(json.dumps(results["search_strategy"], indent=2))
        
        # Print results by source
        if "results_by_source" in results:
            print("\nResults by Source:")
            print("-" * 40)
            for source, entries in results["results_by_source"].items():
                print(f"\n{source}:")
                print("-" * len(source))
                for entry in entries:
                    print(f"Title: {entry['title']}")
                    print(f"URL: {entry['url']}")
                    print(f"Snippet: {entry['snippet']}")
                    print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during legal research: {str(e)}")

if __name__ == "__main__":
    # Verify SERPER_API_KEY is set
    if not os.getenv("SERPER_API_KEY"):
        print("Error: SERPER_API_KEY environment variable is not set")
        print("Please set it in your .env file or environment variables")
        exit(1)
    
    run_legal_search_example()
