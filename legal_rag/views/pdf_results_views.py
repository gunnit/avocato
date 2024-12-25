from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import PDFAnalysisResult

class PDFAnalysisListView(LoginRequiredMixin, ListView):
    model = PDFAnalysisResult
    template_name = 'legal_rag/pdf_analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 10
    
    def get_queryset(self):
        return PDFAnalysisResult.objects.select_related('caso').all()

class PDFAnalysisDetailView(LoginRequiredMixin, DetailView):
    model = PDFAnalysisResult
    template_name = 'legal_rag/pdf_analysis_detail.html'
    context_object_name = 'analysis'
