from django.db import models
from cases.models import Caso
import json

class LegalSearchResult(models.Model):
    """Model for storing comprehensive legal search results from multiple sources"""
    caso = models.ForeignKey(
        Caso, 
        on_delete=models.CASCADE, 
        related_name='legal_search_results'
    )
    search_query = models.JSONField(
        help_text="The case details used for the search"
    )
    search_results = models.JSONField(
        help_text="The complete search results from all sources"
    )
    search_strategy = models.JSONField(
        help_text="The strategy used for the search"
    )
    date_saved = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_saved']
        verbose_name = 'Risultato Ricerca Legale'
        verbose_name_plural = 'Risultati Ricerche Legali'

    def __str__(self):
        return f"Ricerca Legale per {self.caso.titolo} ({self.date_saved.strftime('%Y-%m-%d %H:%M')})"

    @property
    def sources_searched(self) -> list:
        """Get list of sources that were searched"""
        results = self.search_results
        if isinstance(results, str):
            results = json.loads(results)
        return list(results.get('results_by_source', {}).keys())

    @property
    def total_results(self) -> int:
        """Get total number of results found"""
        results = self.search_results
        if isinstance(results, str):
            results = json.loads(results)
        return sum(len(items) for items in results.get('results_by_source', {}).values())

    @property
    def search_terms(self) -> list:
        """Get the search terms used"""
        strategy = self.search_strategy
        if isinstance(strategy, str):
            strategy = json.loads(strategy)
        return strategy.get('terms', [])

    @property
    def summary_by_source(self) -> dict:
        """Get a summary of results count by source"""
        results = self.search_results
        if isinstance(results, str):
            results = json.loads(results)
        return {
            source: len(items)
            for source, items in results.get('results_by_source', {}).items()
        }
