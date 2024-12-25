const analyzeDocument = (function() {
    const showLoading = (button) => {
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Analyzing...
        `;
    };

    const showError = (button, originalHtml) => {
        button.classList.remove('btn-primary');
        button.classList.add('btn-danger');
        button.innerHTML = `
            <i class="ki-duotone ki-cross-circle fs-2">
                <span class="path1"></span>
                <span class="path2"></span>
            </i>
            Analysis Failed
        `;

        setTimeout(() => {
            button.classList.remove('btn-danger');
            button.classList.add('btn-primary');
            button.disabled = false;
            button.innerHTML = originalHtml;
        }, 3000);
    };

    const sendAnalysisRequest = async (data) => {
        const response = await fetch('/legal-rag/analyze-extracted-text/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                analysis_id: data.id,
                text: data.extractedText,
                structured_content: data.structuredContent,
                chunks: data.contentChunks
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.error) {
            throw new Error(result.error);
        }

        return result;
    };

    return async function(analysisData) {
        const button = document.getElementById('analyzeButton');
        const originalHtml = button.innerHTML;

        try {
            showLoading(button);

            const data = {
                analysis_id: analysisData.id,
                text: analysisData.extractedText || null,
                structured_content: analysisData.structuredContent || null,
                chunks: analysisData.contentChunks || null
            };

            const result = await sendAnalysisRequest(data);
            if (result.pages_analyzed > 0) {
                window.location.reload();
            } else {
                throw new Error('No pages were analyzed successfully');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            showError(button, originalHtml);
        }
    };
})();

// Global function to start analysis
window.startAnalysis = function() {
    if (window.ANALYSIS_DATA) {
        analyzeDocument(window.ANALYSIS_DATA);
    } else {
        console.error('Analysis data not found');
    }
};
