import logging
import os
import re
import json
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import pandas as pd
from core.interfaces.enricher import Enricher

@dataclass
class BookMetadata:
    """Class to store Google Books metadata."""
    title: str
    subtitle: Optional[str] = None
    authors: List[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    page_count: Optional[int] = None
    categories: Optional[List[str]] = None
    language: Optional[str] = None
    preview_link: Optional[str] = None
    cover_link: Optional[str] = None
    match_confidence: float = 0.0
    confidence_factors: Dict[str, float] = None


class GoogleBooksEnricher(Enricher):
    """An enricher that uses the Google Books API to enhance ebook metadata.
    
    This enricher implements the Enricher interface from the core module and
    uses Google Books API to retrieve detailed information about books based
    on their titles and authors.
    
    It implements sophisticated searching strategies and confidence scoring
    to ensure high-quality matches even with imperfect input data.
    """
    
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    MAX_RESULTS = 3  # Maximum number of results to consider per book search
    DELAY = 1.0  # Delay between requests to avoid API rate limiting
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Books enricher.
        
        Args:
            api_key: Optional API key for the Google Books API.
                    While the API can be used without a key for limited requests,
                    providing a key enables higher request quotas.
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)
    
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None) -> Optional[str]:
        """
        Enriches the metadata of ebooks in a CSV file using Google Books API.
        
        This method implements the Enricher interface method. It processes a CSV file
        containing basic ebook information, enriches it with data from Google Books,
        and saves the results to a new CSV file.
        
        Args:
            csv_path: Path to the CSV file with basic ebook information
            taxonomy_path: Ignored in this implementation, but required by the interface
            
        Returns:
            Path to the enriched CSV file or None if an error occurred
        """
        if not os.path.exists(csv_path):
            self.logger.error(f"CSV file not found: {csv_path}")
            return None
            
        output_path = csv_path.replace('.csv', '_gb_enriched.csv')
        if output_path == csv_path:
            output_path = os.path.splitext(csv_path)[0] + '_gb_enriched.csv'
        
        try:
            self.logger.info(f"Starting Google Books enrichment for {csv_path}")
            start_time = time.time()
            
            # Read the CSV file
            df = pd.read_csv(csv_path)
            
            # Define columns to keep from the original CSV
            key_columns = ['Nome', 'Formato', 'Tamanho(MB)', 'Data Modificação', 'Caminho']
            extracted_columns = ['Titulo_Extraido', 'Autor_Extraido']
            
            # Create a list of columns to keep
            columns_to_keep = []
            for col in key_columns:
                if col in df.columns:
                    columns_to_keep.append(col)
            
            for col in extracted_columns:
                if col in df.columns:
                    columns_to_keep.append(col)
            
            # Create new DataFrame with only the columns we want to keep
            df_enriched = df[columns_to_keep].copy()
            
            # Add new columns for Google Books metadata
            metadata_columns = [
                'GB_Titulo', 'GB_Subtitulo', 'GB_Autores', 'GB_Editora', 
                'GB_Data_Publicacao', 'GB_ISBN10', 'GB_ISBN13', 'GB_Paginas', 
                'GB_Categorias', 'GB_Idioma', 'GB_Preview_Link', 'GB_Capa_Link', 
                'GB_Confianca_Match', 'GB_Status_Busca'
            ]
            
            for col in metadata_columns:
                df_enriched[col] = None
            
            # Process each row
            total_rows = len(df_enriched)
            matches_found = 0
            
            self.logger.info(f"Processing {total_rows} books")
            
            for idx, row in df_enriched.iterrows():
                # Get the title and author
                title = row.get('Titulo_Extraido', '')
                author = row.get('Autor_Extraido', '')
                
                if not title:
                    # If no extracted title, try to get from filename
                    filename = row.get('Nome', '')
                    title = os.path.splitext(filename)[0]
                
                self.logger.info(f"Processing book {idx + 1}/{total_rows}: {title}")
                
                # Search for the book in Google Books
                metadata = self._search_book(title, author)
                
                if metadata:
                    matches_found += 1
                    df_enriched.at[idx, 'GB_Status_Busca'] = 'Encontrado'
                    df_enriched.at[idx, 'GB_Titulo'] = metadata.title
                    df_enriched.at[idx, 'GB_Subtitulo'] = metadata.subtitle
                    df_enriched.at[idx, 'GB_Autores'] = ', '.join(metadata.authors) if metadata.authors else None
                    df_enriched.at[idx, 'GB_Editora'] = metadata.publisher
                    df_enriched.at[idx, 'GB_Data_Publicacao'] = metadata.published_date
                    df_enriched.at[idx, 'GB_ISBN10'] = metadata.isbn_10
                    df_enriched.at[idx, 'GB_ISBN13'] = metadata.isbn_13
                    df_enriched.at[idx, 'GB_Paginas'] = metadata.page_count
                    df_enriched.at[idx, 'GB_Categorias'] = ', '.join(metadata.categories) if metadata.categories else None
                    df_enriched.at[idx, 'GB_Idioma'] = metadata.language
                    df_enriched.at[idx, 'GB_Preview_Link'] = metadata.preview_link
                    df_enriched.at[idx, 'GB_Capa_Link'] = metadata.cover_link
                    df_enriched.at[idx, 'GB_Confianca_Match'] = metadata.match_confidence
                else:
                    df_enriched.at[idx, 'GB_Status_Busca'] = 'Não Encontrado'
                
                # Log progress after every 10 books or at the end
                if (idx + 1) % 10 == 0 or idx == total_rows - 1:
                    success_rate = (matches_found / (idx + 1)) * 100
                    self.logger.info(f"Progress: {idx + 1}/{total_rows} ({(idx + 1)/total_rows*100:.1f}%)")
                    self.logger.info(f"Success rate so far: {success_rate:.1f}%")
            
            # Save the enriched CSV
            df_enriched.to_csv(output_path, index=False, encoding='utf-8')
            
            # Log final statistics
            elapsed_time = time.time() - start_time
            success_rate = (matches_found / total_rows) * 100
            
            self.logger.info(f"Enrichment completed in {elapsed_time:.2f} seconds")
            self.logger.info(f"Found metadata for {matches_found}/{total_rows} books ({success_rate:.1f}%)")
            self.logger.info(f"Enriched CSV saved to {output_path}")
            
            # Generate a metadata summary
            self._generate_summary(df_enriched, matches_found, total_rows)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error enriching data: {str(e)}")
            return None
    
    def _throttle_request(self):
        """
        Implements delay between API requests to avoid rate limiting.
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.DELAY:
            time.sleep(self.DELAY - time_since_last)
        self.last_request_time = time.time()
    
    def _try_search(self, query: str, lang_restrict: Optional[str] = None) -> Optional[BookMetadata]:
        """
        Attempts a specific search in Google Books.
        
        Args:
            query: The search query string
            lang_restrict: Optional language restriction (e.g., 'pt-BR', 'en')
            
        Returns:
            BookMetadata object if a match is found, None otherwise
        """
        try:
            params = {
                'q': query,
                'maxResults': self.MAX_RESULTS,
                'printType': 'books'
            }
            
            if lang_restrict:
                params['langRestrict'] = lang_restrict
                
            if self.api_key:
                params['key'] = self.api_key
                
            self.logger.debug(f"Trying search with query: {query}" + 
                            (f" (language: {lang_restrict})" if lang_restrict else ""))
            
            self._throttle_request()
            response = self.session.get(
                self.BASE_URL,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            total_items = data.get('totalItems', 0)
            self.logger.debug(f"Found {total_items} results")
            
            if total_items == 0:
                return None
            
            best_match = None
            highest_confidence = 0
            best_confidence_factors = None
            
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                confidence, confidence_factors = self._calculate_match_confidence(
                    volume_info,
                    query,
                    None
                )
                
                self.logger.debug(f"Analyzing result: '{volume_info.get('title')}' (Confidence: {confidence:.2f})")
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = volume_info
                    best_confidence_factors = confidence_factors
            
            if best_match and highest_confidence > 0.3:
                return self._parse_volume_info(best_match, highest_confidence, best_confidence_factors)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error in search '{query}': {str(e)}")
            return None
    
    def _search_book(self, title: str, author: Optional[str] = None) -> Optional[BookMetadata]:
        """
        Searches for a book in Google Books using multiple strategies.
        
        This method implements a series of search strategies with decreasing specificity
        to maximize the chance of finding a match.
        
        Args:
            title: The book title
            author: Optional author name
            
        Returns:
            BookMetadata object if a match is found, None otherwise
        """
        if not title:
            self.logger.warning("Empty title provided, skipping search")
            return None
            
        # Clean up inputs
        title = title.strip()
        if author and author.strip().lower() == "desconhecido":
            author = None
        elif author:
            author = author.strip()
            
        self.logger.info(f"Searching for: '{title}'" + (f" by '{author}'" if author else ""))
        
        search_strategies = [
            # 1. Search in Portuguese with title and author
            lambda: self._try_search(f'intitle:"{title}"' + 
                                   (f' inauthor:"{author}"' if author else ''), 
                                   'pt-BR'),
            
            # 2. Search in any language with title and author
            lambda: self._try_search(f'intitle:"{title}"' + 
                                   (f' inauthor:"{author}"' if author else '')),
            
            # 3. Search in Portuguese with exact title
            lambda: self._try_search(f'"{title}"', 'pt-BR'),
            
            # 4. Search in any language with exact title
            lambda: self._try_search(f'"{title}"'),
            
            # 5. Search in Portuguese with title keywords
            lambda: self._try_search(' '.join(title.split()[:3]), 'pt-BR'),
            
            # 6. Search in any language with title keywords
            lambda: self._try_search(' '.join(title.split()[:3])),
            
            # 7. Search with title without special characters
            lambda: self._try_search(re.sub(r'[^\w\s]', ' ', title))
        ]
        
        for i, strategy in enumerate(search_strategies):
            self.logger.debug(f"Trying search strategy {i+1}")
            result = strategy()
            if result:
                self.logger.info(f"Found match using strategy {i+1}")
                return result
            
        self.logger.info(f"No results found for: '{title}'" + (f" by '{author}'" if author else ""))
        return None
    
    def _calculate_match_confidence(
        self, 
        volume_info: Dict[str, Any],
        search_query: str,
        search_author: Optional[str]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates confidence score for the match between result and search.
        
        Args:
            volume_info: The book information from Google Books API
            search_query: The search query used
            search_author: The author used in the search (if any)
            
        Returns:
            Tuple of (confidence_score, confidence_factors)
        """
        confidence_factors = {}
        
        # Get book information
        book_title = volume_info.get('title', '').lower()
        book_subtitle = volume_info.get('subtitle', '').lower()
        search_query = search_query.lower()
        
        # Clean text for comparison
        clean_query = re.sub(r'[^\w\s]', ' ', search_query)
        clean_title = re.sub(r'[^\w\s]', ' ', book_title)
        clean_subtitle = re.sub(r'[^\w\s]', ' ', book_subtitle) if book_subtitle else ''
        
        # Split into words
        query_words = set(clean_query.split())
        title_words = set(clean_title.split())
        subtitle_words = set(clean_subtitle.split()) if clean_subtitle else set()
        
        # Calculate title similarity
        title_common_words = query_words.intersection(title_words)
        if title_common_words:
            title_ratio = len(title_common_words) / max(len(query_words), len(title_words))
            confidence_factors['title_match'] = 0.3 + (0.4 * title_ratio)
            
            # Bonus for long words matches in title
            long_words = [w for w in title_common_words if len(w) > 5]
            if long_words:
                confidence_factors['title_long_words'] = 0.1 * min(len(long_words), 2)
        else:
            confidence_factors['title_match'] = 0.0
            confidence_factors['title_long_words'] = 0.0
            
        # Calculate subtitle similarity if exists
        if subtitle_words:
            subtitle_common_words = query_words.intersection(subtitle_words)
            if subtitle_common_words:
                subtitle_ratio = len(subtitle_common_words) / max(len(query_words), len(subtitle_words))
                confidence_factors['subtitle_match'] = 0.2 * subtitle_ratio
                
                # Bonus for long words matches in subtitle
                long_words = [w for w in subtitle_common_words if len(w) > 5]
                if long_words:
                    confidence_factors['subtitle_long_words'] = 0.05 * min(len(long_words), 2)
            else:
                confidence_factors['subtitle_match'] = 0.0
                confidence_factors['subtitle_long_words'] = 0.0
        
        # Calculate exact match bonus
        if clean_query in clean_title or clean_title in clean_query:
            confidence_factors['exact_match'] = 0.2
        elif clean_query in clean_subtitle or clean_subtitle in clean_query:
            confidence_factors['exact_match'] = 0.1
        else:
            confidence_factors['exact_match'] = 0.0
        
        # Calculate total confidence
        total_confidence = sum(confidence_factors.values())
        
        return min(total_confidence, 1.0), confidence_factors
    
    def _parse_volume_info(self, volume_info: Dict[str, Any], confidence: float, confidence_factors: Dict[str, float]) -> BookMetadata:
        """
        Extracts relevant metadata from volume_info returned by the API.
        
        Args:
            volume_info: The volumeInfo part of the Google Books API response
            confidence: The calculated confidence score
            confidence_factors: The detailed confidence factors
            
        Returns:
            BookMetadata object with parsed information
        """
        # Extract ISBNs
        industry_identifiers = volume_info.get('industryIdentifiers', [])
        isbn_10 = next((i['identifier'] for i in industry_identifiers if i['type'] == 'ISBN_10'), None)
        isbn_13 = next((i['identifier'] for i in industry_identifiers if i['type'] == 'ISBN_13'), None)
        
        # Extract cover link (prefer larger version if available)
        image_links = volume_info.get('imageLinks', {})
        cover_link = (
            image_links.get('large') or 
            image_links.get('medium') or 
            image_links.get('thumbnail') or 
            image_links.get('smallThumbnail')
        )
        
        return BookMetadata(
            title=volume_info.get('title', ''),
            subtitle=volume_info.get('subtitle'),
            authors=volume_info.get('authors', []),
            publisher=volume_info.get('publisher'),
            published_date=volume_info.get('publishedDate'),
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            page_count=volume_info.get('pageCount'),
            categories=volume_info.get('categories', []),
            language=volume_info.get('language'),
            preview_link=volume_info.get('previewLink'),
            cover_link=cover_link,
            match_confidence=confidence,
            confidence_factors=confidence_factors
        )
    
    def _generate_summary(self, df: pd.DataFrame, matches_found: int, total_rows: int) -> None:
        """
        Generates a summary of the enrichment process.
        
        Args:
            df: The enriched DataFrame
            matches_found: Number of successful matches
            total_rows: Total number of processed rows
        """
        success_rate = (matches_found / total_rows) * 100
        
        # Basic statistics
        self.logger.info("=== Google Books Enrichment Summary ===")
        self.logger.info(f"Total Books: {total_rows}")
        self.logger.info(f"Successful Matches: {matches_found} ({success_rate:.1f}%)")
        
        # More detailed statistics if we have matches
        if matches_found > 0:
            # Language distribution
            if 'GB_Idioma' in df.columns:
                languages = df['GB_Idioma'].value_counts()
                self.logger.info("Language Distribution:")
                for lang, count in languages.items():
                    if pd.notna(lang):
                        self.logger.info(f"  {lang}: {count} ({count/matches_found*100:.1f}%)")
            
            # Publisher distribution (top 5)
            if 'GB_Editora' in df.columns:
                publishers = df['GB_Editora'].value_counts().head(5)
                self.logger.info("Top 5 Publishers:")
                for pub, count in publishers.items():
                    if pd.notna(pub):
                        self.logger.info(f"  {pub}: {count}")
            
            # Average match confidence
            if 'GB_Confianca_Match' in df.columns:
                avg_confidence = df['GB_Confianca_Match'].mean()
                self.logger.info(f"Average Match Confidence: {avg_confidence:.2f}")