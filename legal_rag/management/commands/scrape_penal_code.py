import re
import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from legal_rag.models import PenalCodeBook, PenalCodeTitle, PenalCodeSection, PenalCodeArticle
from urllib.parse import urljoin
from django.db import transaction

class Command(BaseCommand):
    help = 'Scrapes the Italian Penal Code from brocardi.it'

    def handle(self, *args, **options):
        base_url = 'https://www.brocardi.it/codice-penale/'
        
        def get_soup(url):
            self.stdout.write(f'Fetching URL: {url}')
            # Add shorter delay to be respectful to the server
            time.sleep(0.5)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                self.stdout.write(f'Successfully fetched {url}')
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'Error fetching {url}: {str(e)}'))
                raise

        def extract_article_content(article_url):
            soup = get_soup(article_url)
            
            # Extract article description (subtitle)
            description = ""
            subtitle = soup.find('div', class_='subtitle')
            if subtitle:
                description = subtitle.get_text(strip=True)
            
            # Extract article content
            content = ""
            content_div = soup.find('div', {'class': 'articolo'}) or soup.find('div', {'class': 'text'})
            if content_div:
                content = content_div.get_text(strip=True)
            
            # Extract section info from breadcrumb
            section_info = None
            breadcrumb = soup.find('div', {'id': 'breadcrumb'})
            if breadcrumb:
                section_link = breadcrumb.find('a', text=re.compile(r'Sezione [IVX]+'))
                if section_link:
                    section_text = section_link.get_text(strip=True)
                    section_match = re.match(r'Sezione ([IVX]+) - (.+)', section_text)
                    if section_match:
                        section_info = {
                            'number': self.roman_to_int(section_match.group(1)),
                            'name': section_match.group(2)
                        }
            
            return content, description, section_info

        try:
            self.stdout.write('Starting scraping process...')
            soup = get_soup(base_url)
            
            # Find all book links (they contain "LIBRO" in the text)
            book_links = soup.find_all('a', text=re.compile(r'LIBRO \w+'))
            self.stdout.write(f'Found {len(book_links)} books')
            
            for book_link in book_links:
                book_text = book_link.get_text(strip=True)
                book_match = re.match(r'LIBRO (\w+) - (.+)', book_text)
                if not book_match:
                    self.stdout.write(self.style.WARNING(f'Could not parse book info from: {book_text}'))
                    continue
                
                book_num = book_match.group(1)  # PRIMO, SECONDO, etc.
                book_name = book_match.group(2)
                
                # Convert Italian ordinal numbers to Roman numerals
                italian_to_roman = {
                    'PRIMO': 'I', 'SECONDO': 'II', 'TERZO': 'III',
                    'QUARTO': 'IV', 'QUINTO': 'V', 'SESTO': 'VI'
                }
                book_roman = italian_to_roman.get(book_num, book_num)
                
                # Save book immediately
                book, created = PenalCodeBook.objects.get_or_create(
                    number=self.roman_to_int(book_roman),
                    defaults={
                        'name': book_name,
                        'description': book_text
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created book: {book}'))
                else:
                    self.stdout.write(f'Found existing book: {book}')

                # Get the book's page
                book_url = urljoin(base_url, book_link.get('href', ''))
                if not book_url:
                    self.stdout.write(self.style.WARNING(f'No URL found for book: {book_text}'))
                    continue

                book_soup = get_soup(book_url)
                
                current_title = None
                current_section = None
                
                # Look for all links that might be articles
                article_links = book_soup.find_all('a', href=re.compile(r'art\d+'))
                
                for link in article_links:
                    article_text = link.get_text(strip=True)
                    # Check if this is a title marker
                    title_match = re.match(r'Titolo ([IVX]+) -\s*(.+?)(?:\s*\(artt\.\s*(\d+)-(\d+)\))?$', article_text)
                    
                    if title_match:
                        # Create new title
                        title_num = title_match.group(1)
                        title_name = title_match.group(2)
                        current_title, created = PenalCodeTitle.objects.get_or_create(
                            book=book,
                            number=self.roman_to_int(title_num),
                            defaults={
                                'name': title_name,
                                'articles_range': ''  # Will be updated later
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created title: {current_title}'))
                        else:
                            self.stdout.write(f'Found existing title: {current_title}')
                        
                    else:
                        # This should be an article
                        article_match = re.match(r'Art\.\s*(\d+)\s*—\s*(.+)', article_text)
                        if article_match:
                            art_num = int(article_match.group(1))
                            art_heading = article_match.group(2)
                            
                            # Skip if article already exists
                            if PenalCodeArticle.objects.filter(number=art_num, title__book=book).exists():
                                self.stdout.write(f'Skipping existing article {art_num}')
                                continue
                            
                            # Get article content and section info
                            article_url = urljoin(book_url, link.get('href', ''))
                            content, description, section_info = extract_article_content(article_url)
                            
                            if not current_title:
                                # Create a default title if none exists
                                current_title, _ = PenalCodeTitle.objects.get_or_create(
                                    book=book,
                                    number=1,  # Default number
                                    defaults={
                                        'name': 'Disposizioni Generali',  # Default name
                                        'articles_range': ''
                                    }
                                )
                                self.stdout.write(self.style.SUCCESS(f'Created default title for book {book.number}'))
                            
                            # Handle section if present
                            if section_info:
                                current_section, created = PenalCodeSection.objects.get_or_create(
                                    title=current_title,
                                    number=section_info['number'],
                                    defaults={'name': section_info['name']}
                                )
                                if created:
                                    self.stdout.write(self.style.SUCCESS(f'Created section: {current_section}'))
                                else:
                                    self.stdout.write(f'Found existing section: {current_section}')
                            
                            # Save article immediately
                            article = PenalCodeArticle.objects.create(
                                title=current_title,
                                section=current_section if section_info else None,
                                number=art_num,
                                heading=art_heading,
                                description=description,
                                content=content
                            )
                            self.stdout.write(self.style.SUCCESS(f'Created article: {article}'))

            self.stdout.write(self.style.SUCCESS('Scraping completed successfully'))

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nScraping interrupted by user. Progress has been saved.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Scraping failed: {str(e)}'))
            raise

    def roman_to_int(self, roman):
        roman_values = {
            'I': 1, 'V': 5, 'X': 10,
            'L': 50, 'C': 100, 'D': 500, 'M': 1000
        }
        
        total = 0
        prev_value = 0
        
        for char in reversed(roman):
            curr_value = roman_values[char]
            if curr_value >= prev_value:
                total += curr_value
            else:
                total -= curr_value
            prev_value = curr_value
            
        return total
