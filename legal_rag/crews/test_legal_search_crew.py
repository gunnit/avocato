import os
import django
import unittest

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_assistant.settings.local')
django.setup()

from legal_rag.crews.legal_search_crew import LegalSearchCrew
from legal_rag.models.legal_search import LegalSearchResult

class TestLegalSearchCrew(unittest.TestCase):
    def setUp(self):
        self.crew = LegalSearchCrew()
        
    def test_search_results(self):
        # Test case data
        case_details = {
            "title": "rapina a mano armata",
            "description": "Caso di rapina a mano armata con uso di armi da fuoco"
        }
        
        # Execute search
        results = self.crew.kickoff(case_details)
        
        # Verify results structure
        self.assertIn("results_by_source", results)
        self.assertIsInstance(results["results_by_source"], dict)
        
        # Verify results content
        source = "giurisprudenzapenale.com"
        if source in results["results_by_source"]:
            for result in results["results_by_source"][source]:
                self.assertIn("title", result)
                self.assertIn("url", result)
                self.assertIn("snippet", result)
                self.assertTrue(result["url"].startswith("https://www.giurisprudenzapenale.com"))
        
        # Verify results are not empty
        self.assertGreater(len(results["results_by_source"].get(source, [])), 0,
                         "No results found from giurisprudenzapenale.com")
        
        # Save results to database
        # Create a dummy Caso instance for testing
        from cases.models import Caso
        test_case = Caso.objects.create(
            titolo="Test Case",
            descrizione="Test Description",
            analisi_legale="Test Legal Analysis"
        )
        
        search_result = LegalSearchResult.objects.create(
            caso=test_case,
            search_query=case_details,
            search_results=results,
            search_strategy={}
        )
        
        # Verify saved results
        saved_result = LegalSearchResult.objects.get(id=search_result.id)
        self.assertEqual(saved_result.search_results, results)
        self.assertEqual(len(saved_result.search_results["results_by_source"][source]),
                        len(results["results_by_source"][source]))

if __name__ == '__main__':
    unittest.main()
