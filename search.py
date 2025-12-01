import time
import json
import re
from typing import List, Dict, Optional
from scholarly import scholarly
from database import get_db
from models import Paper, SearchResult
from config import Config

class SearchService:
    
    @staticmethod
    def search_internal(query: str, tags: Optional[List[str]] = None, 
                       year_from: Optional[int] = None, 
                       asip_funded_only: bool = False) -> List[Paper]:
        """Search internal PDF database"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Build SQL query dynamically
            sql = """
                SELECT * FROM papers 
                WHERE (
                    title LIKE ? OR 
                    authors LIKE ? OR 
                    abstract LIKE ? OR 
                    pdf_text LIKE ?
                )
            """
            params = [f'%{query}%'] * 4
            
            # Add filters
            if tags:
                tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
                sql += f" AND ({tag_conditions})"
                params.extend([f'%{tag}%' for tag in tags])
            
            if year_from:
                sql += " AND year >= ?"
                params.append(year_from)
            
            if asip_funded_only:
                sql += " AND asip_funded = TRUE"
            
            sql += " ORDER BY year DESC, citation_count DESC LIMIT 50"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [Paper.from_db_row(row) for row in rows]
    
    @staticmethod
    def search_google_scholar(query: str, max_results: int = 20) -> List[Dict]:
        """Search Google Scholar (free API via scholarly)"""
        results = []
        
        try:
            search_query = scholarly.search_pubs(query)
            
            for i, pub in enumerate(search_query):
                if i >= max_results:
                    break
                
                bib = pub.get('bib', {})
                
                # Extract year safely
                year = bib.get('pub_year', 'N/A')
                if year == 'N/A':
                    year = 2024  # Default for display purposes
                
                results.append({
                    'title': bib.get('title', 'N/A'),
                    'authors': ', '.join(bib.get('author', [])),
                    'abstract': bib.get('abstract', '')[:500],
                    'year': year,
                    'source': 'Google Scholar',
                    'url': pub.get('pub_url', ''),
                    'citation_count': pub.get('num_citations', 0)
                })
        except Exception as e:
            print(f"❌ Google Scholar search error: {e}")
        
        return results
    
    @staticmethod
    def check_api_limit(service: str) -> bool:
        """Check if API usage is under monthly limit"""
        current_month = time.strftime('%Y-%m')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT call_count FROM api_usage 
                WHERE service = ? AND month = ?
            """, (service, current_month))
            
            row = cursor.fetchone()
            
            if not row:
                # Initialize counter for new month
                cursor.execute("""
                    INSERT INTO api_usage (service, month, call_count) 
                    VALUES (?, ?, 0)
                """, (service, current_month))
                return True
            
            return row['call_count'] < Config.PERPLEXITY_MONTHLY_LIMIT
    
    @staticmethod
    def increment_api_usage(service: str):
        """Increment API usage counter"""
        current_month = time.strftime('%Y-%m')
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE api_usage 
                SET call_count = call_count + 1, updated_at = CURRENT_TIMESTAMP 
                WHERE service = ? AND month = ?
            """, (service, current_month))
    
    @staticmethod
    def unified_search(query: str, sources: List[str], 
                      tags: Optional[List[str]] = None,
                      year_from: Optional[int] = None,
                      asip_funded_only: bool = False,
                      user_id: Optional[int] = None) -> SearchResult:
        """Unified search across multiple sources"""
        start_time = time.time()
        all_papers = []
        sources_used = []
        
        # Search internal database
        if 'internal' in sources:
            internal_results = SearchService.search_internal(
                query, tags, year_from, asip_funded_only
            )
            all_papers.extend(internal_results)
            sources_used.append('internal')
        
        # Search Google Scholar
        if 'scholar' in sources:
            scholar_results = SearchService.search_google_scholar(query)
            # Convert dicts to Paper objects (simplified)
            for result in scholar_results:
                paper = Paper(
                    id=0,  # Not in DB yet
                    title=result['title'],
                    authors=result['authors'],
                    abstract=result['abstract'],
                    year=result['year'],
                    source='Google Scholar',
                    arxiv_id=None,
                    doi=None,
                    pdf_path=None,
                    pdf_text=None,
                    asip_funded=False,
                    tags=[],
                    citation_count=result['citation_count'],
                    added_by=None,
                    created_at=''
                )
                all_papers.append(paper)
            sources_used.append('Google Scholar')
        
        # Log search
        if user_id:
            SearchService.log_search(user_id, query, sources_used, len(all_papers))
        
        execution_time = time.time() - start_time
        
        return SearchResult(
            papers=all_papers,
            total_count=len(all_papers),
            query=query,
            sources_used=sources_used,
            execution_time=execution_time
        )
    
    @staticmethod
    def log_search(user_id: int, query: str, sources: List[str], result_count: int):
        """Log search for analytics"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_logs (user_id, query, sources, result_count)
                VALUES (?, ?, ?, ?)
            """, (user_id, query, json.dumps(sources), result_count))
