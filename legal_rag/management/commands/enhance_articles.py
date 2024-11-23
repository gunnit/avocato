import os
import re
from openai import OpenAI
from django.core.management.base import BaseCommand
from legal_rag.models import PenalCodeArticle
from django.conf import settings

class Command(BaseCommand):
    help = 'Enhance article descriptions using OpenAI while maintaining exact content'

    def normalize_text(self, text):
        """Normalize text for comparison by removing HTML tags, extra spaces, and normalizing punctuation"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        # Remove extra spaces around punctuation
        text = re.sub(r'\s*([.,;:?!])\s*', r'\1 ', text)
        # Trim and lowercase
        return text.strip().lower()

    def debug_content_difference(self, original, enhanced):
        """Debug differences between original and enhanced content"""
        norm_original = self.normalize_text(original)
        norm_enhanced = self.normalize_text(enhanced)
        
        if norm_original != norm_enhanced:
            self.stdout.write(self.style.WARNING("Content difference detected:"))
            self.stdout.write("Original (normalized):")
            self.stdout.write(norm_original)
            self.stdout.write("\nEnhanced (normalized):")
            self.stdout.write(norm_enhanced)
            return False
        return True

    def handle(self, *args, **options):
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Get all articles
        articles = PenalCodeArticle.objects.all()
        total = articles.count()
        
        self.stdout.write(f"Found {total} articles to enhance")

        for i, article in enumerate(articles, 1):
            self.stdout.write(f"Processing article {i}/{total}: Art. {article.number}")
            
            try:
                # Prepare system prompt with specific formatting rules
                system_prompt = """You are a legal document formatter specializing in Italian Penal Code articles. Your task is to enhance the formatting of legal articles while maintaining their EXACT content and meaning. Follow these strict rules:

1. CRITICAL: DO NOT modify any text content. The text must remain EXACTLY the same.
   - Do not change any words
   - Do not modify punctuation
   - Do not rearrange text
   - Only add HTML formatting tags

2. Formatting Structure:
   - Wrap each paragraph in <p> tags
   - Use <strong> for article numbers and key terms
   - Use <div class="indent-[1-3]"> for indentation levels
   - Preserve all line breaks and spacing

3. HTML Tag Usage:
   - <p> - for paragraphs
   - <strong> - for emphasis (article numbers and key terms)
   - <div class="legal-section"> - for major sections
   - <div class="indent-1/2/3"> - for indentation levels
   - <ul>/<li> - for lists (only if original text has bullet points)

Example (showing exact text preservation):
Original: "Art. 1. - Reati e pene"
Formatted: <p><strong>Art. 1.</strong> - <strong>Reati e pene</strong></p>

Original: "Nessuno può essere punito per un fatto che non sia espressamente preveduto come reato dalla legge."
Formatted: <p>Nessuno può essere punito per un fatto che non sia espressamente preveduto come <strong>reato</strong> dalla <strong>legge</strong>.</p>

REMEMBER: The text content must remain EXACTLY the same. Only add HTML tags for formatting."""

                # Prepare user prompt
                user_prompt = f"""Format this legal article by adding HTML tags while keeping the EXACT same text content:

{article.content}

IMPORTANT:
1. Do not change any words or punctuation
2. Only add HTML formatting tags
3. Preserve exact spacing and line breaks
4. Return the complete text with only formatting changes"""

                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1  # Very low temperature for consistent formatting
                )

                # Extract enhanced content
                enhanced_content = response.choices[0].message.content.strip()

                # Verify content hasn't been altered using normalized comparison
                if not self.debug_content_difference(article.content, enhanced_content):
                    raise ValueError("Content was altered during formatting")

                # Update article
                article.content = enhanced_content
                article.save()

                self.stdout.write(self.style.SUCCESS(f"Successfully enhanced article {article.number}"))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing article {article.number}: {str(e)}")
                )
                continue

        self.stdout.write(self.style.SUCCESS("Finished enhancing all articles"))
