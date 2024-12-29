from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from legal_rag.models import LegalSearchResult
from cases.models import Caso
from legal_rag.crews.legal_search_crew import LegalSearchCrew
import json

class LegalSearchResultsView(LoginRequiredMixin, ListView):
    """View to display legal search results for a case"""
    model = LegalSearchResult
    template_name = 'legal_rag/legal_search_results.html'
    context_object_name = 'search_results'

    def get_queryset(self):
        caso_id = self.kwargs.get('caso_id')
        return LegalSearchResult.objects.filter(caso_id=caso_id).order_by('-date_saved')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['caso'] = get_object_or_404(Caso, id=self.kwargs.get('caso_id'))
        return context

class LegalSearchDetailView(LoginRequiredMixin, DetailView):
    """View to display detailed results of a specific legal search"""
    model = LegalSearchResult
    template_name = 'legal_rag/legal_search_detail.html'
    context_object_name = 'search_result'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Always get the caso object
        caso_id = self.kwargs.get('caso_id')
        if caso_id:
            context['caso'] = get_object_or_404(Caso, id=caso_id)
        
        try:
            search_result = self.get_object()
            if search_result:
                # Parse JSON fields for template display
                context['search_query'] = json.loads(search_result.search_query) if isinstance(search_result.search_query, str) else search_result.search_query
                context['search_results'] = json.loads(search_result.search_results) if isinstance(search_result.search_results, str) else search_result.search_results
                context['search_strategy'] = json.loads(search_result.search_strategy) if isinstance(search_result.search_strategy, str) else search_result.search_strategy
            else:
                context['search_results'] = None
                
        except (LegalSearchResult.DoesNotExist, AttributeError):
            context['search_results'] = None
            
        return context

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except (LegalSearchResult.DoesNotExist, AttributeError):
            return None
