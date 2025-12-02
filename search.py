import time
import json
import re
import signal
from typing import List, Dict, Optional
from scholarly import scholarly
from database import get_db
from psycopg2.extras import RealDictCursor
from models import Paper, SearchResult
from config import Config

def timeout_handler(signum, frame):
    raise TimeoutError("Google Scholar search timed out")

class SearchService:
    
    @staticmethod
    def search_internal(query: str, tags: Optional[List[str]] = None, 
                       year_from: Optional[int] = None, 
                       asip_funded_only: bool = False) -> List[Paper]:
        """Search internal PDF database"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build SQL query dynamically
            sql = """
                SELECT * FROM papers 
                WHERE (
                    title LIKE %s OR 
                    authors LIKE %s OR 
                    abstract LIKE %s OR 
                    pdf_text LIKE %s
                )
            """
            params = [f'%{query}%'] * 4
            
            # Add filters
            if tags:
                tag_conditions = " OR ".join(["tags LIKE %s" for _ in tags])
                sql += f" AND ({tag_conditions})"
                params.extend([f'%{tag}%' for tag in tags])
            
            if year_from:
                sql += " AND year >= %s"
                params.append(year_from)
            
            if asip_funded_only:
                sql += " AND asip_funded = TRUE"
            
            sql += " ORDER BY year DESC, citation_count DESC LIMIT 50"
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            
            return [Paper.from_db_row(row) for row in rows]
    
    @staticmethod
    def search_google_scholar(query: str, max_results: int = 20) -> List[Dict]:
        """Search Google Scholar (free API via scholarly)"""
        results = []
        
        try:
            # Set a 10-second timeout for Google Scholar API
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)
            
            try:
                search_query = scholarly.search_pubs(query)
                count = 0
                
                for pub in search_query:
                    if count >= max_results:
                        break
                    
                    try:
                        bib = pub.get('bib', {})
                        
                        # Extract year safely
                        year = bib.get('pub_year', 'N/A')
                        if year == 'N/A':
                            year = 2024  # Default for display purposes
                        
                        results.append({
                            'title': bib.get('title', 'N/A'),
                            'authors': ', '.join(bib.get('author', [])) if bib.get('author') else 'Unknown',
                            'abstract': bib.get('abstract', '')[:500] if bib.get('abstract') else '',
                            'year': year,
                            'source': 'Google Scholar',
                            'url': pub.get('pub_url', ''),
                            'citation_count': pub.get('num_citations', 0)
                        })
                        count += 1
                    except Exception as pub_error:
                        print(f"⚠️ Error parsing Google Scholar result: {pub_error}")
                        continue
                
                signal.alarm(0)  # Cancel alarm
            
            except TimeoutError:
                signal.alarm(0)
                print(f"⚠️ Google Scholar search timed out after 10 seconds for query: {query}")
                print(f"   This may be due to Google Scholar rate limiting. Try again in a few moments.")
                
        except Exception as e:
            signal.alarm(0)
            print(f"⚠️ Google Scholar API error: {type(e).__name__}: {str(e)[:100]}")
        
        return results
    
    @staticmethod
    def check_api_limit(service: str) -> bool:
        """Check if API usage is under monthly limit"""
        current_month = time.strftime('%Y-%m')
        
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT call_count FROM api_usage 
                WHERE service = %s AND month = %s
            """, (service, current_month))
            
            row = cursor.fetchone()
            
            if not row:
                # Initialize counter for new month
                cursor.execute("""
                    INSERT INTO api_usage (service, month, call_count) 
                    VALUES (%s, %s, 0)
                """, (service, current_month))
                return True
            
            return row['call_count'] < Config.PERPLEXITY_MONTHLY_LIMIT
    
    @staticmethod
    def increment_api_usage(service: str):
        """Increment API usage counter"""
        current_month = time.strftime('%Y-%m')
        
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                UPDATE api_usage 
                SET call_count = call_count + 1, updated_at = CURRENT_TIMESTAMP 
                WHERE service = %s AND month = %s
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
            for result in scholar_results:
                paper = Paper(
                    id=0,
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
                    created_at='',
                    url=result.get('url', '')
                )
                all_papers.append(paper)
            sources_used.append('Google Scholar')
        
        # Search arXiv
        if 'arxiv' in sources:
            arxiv_results = SearchService.search_arxiv(query)
            for result in arxiv_results:
                paper = Paper(
                    id=0,
                    title=result['title'],
                    authors=result['authors'],
                    abstract=result['abstract'],
                    year=result['year'],
                    source='arXiv',
                    arxiv_id=result.get('arxiv_id'),
                    doi=None,
                    pdf_path=None,
                    pdf_text=None,
                    asip_funded=False,
                    tags=[],
                    citation_count=0,
                    added_by=None,
                    created_at='',
                    url=result.get('url', '')
                )
                all_papers.append(paper)
            sources_used.append('arXiv')
        
        # Search CrossRef
        if 'crossref' in sources:
            crossref_results = SearchService.search_crossref(query)
            for result in crossref_results:
                paper = Paper(
                    id=0,
                    title=result['title'],
                    authors=result['authors'],
                    abstract=result['abstract'],
                    year=result['year'],
                    source='CrossRef',
                    arxiv_id=None,
                    doi=result.get('doi'),
                    pdf_path=None,
                    pdf_text=None,
                    asip_funded=False,
                    tags=[],
                    citation_count=0,
                    added_by=None,
                    created_at='',
                    url=result.get('url', '')
                )
                all_papers.append(paper)
            sources_used.append('CrossRef')
        
        # Search Semantic Scholar
        if 'semantic_scholar' in sources:
            semantic_results = SearchService.search_semantic_scholar(query)
            for result in semantic_results:
                paper = Paper(
                    id=0,
                    title=result['title'],
                    authors=result['authors'],
                    abstract=result['abstract'],
                    year=result['year'],
                    source='Semantic Scholar',
                    arxiv_id=None,
                    doi=result.get('doi'),
                    pdf_path=None,
                    pdf_text=None,
                    asip_funded=False,
                    tags=[],
                    citation_count=result.get('citation_count', 0),
                    added_by=None,
                    created_at='',
                    url=result.get('url', '')
                )
                all_papers.append(paper)
            sources_used.append('Semantic Scholar')
        
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
    def search_arxiv(query: str, max_results: int = 20) -> List[Dict]:
        """Search arXiv API (free, no API key needed)"""
        results = []
        try:
            import urllib.request
            search_url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
            response = urllib.request.urlopen(search_url, timeout=10)
            data = response.read().decode('utf-8')
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text
                authors = [a.find('{http://www.w3.org/2005/Atom}name').text 
                          for a in entry.findall('{http://www.w3.org/2005/Atom}author')]
                abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/abs/')[-1]
                published = entry.find('{http://www.w3.org/2005/Atom}published').text[:4]
                
                results.append({
                    'title': title,
                    'authors': ', '.join(authors),
                    'abstract': abstract[:500],
                    'year': int(published),
                    'arxiv_id': arxiv_id,
                    'url': f'https://arxiv.org/abs/{arxiv_id}'
                })
        except Exception as e:
            print(f"⚠️ arXiv search error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    @staticmethod
    def search_crossref(query: str, max_results: int = 20) -> List[Dict]:
        """Search CrossRef API (free, no API key needed)"""
        results = []
        try:
            import urllib.request, urllib.parse
            search_url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows={max_results}"
            response = urllib.request.urlopen(search_url, timeout=10)
            data = response.read().decode('utf-8')
            
            import json as json_module
            response_data = json_module.loads(data)
            
            for item in response_data.get('message', {}).get('items', []):
                results.append({
                    'title': item.get('title', ['N/A'])[0] if item.get('title') else 'N/A',
                    'authors': ', '.join([f"{a.get('family', '')} {a.get('given', '')}".strip() 
                                         for a in item.get('author', [])]) or 'Unknown',
                    'abstract': item.get('abstract', '')[:500] or '',
                    'year': item.get('published-online', {}).get('date-parts', [[2024]])[0][0],
                    'doi': item.get('DOI', ''),
                    'url': item.get('URL', '')
                })
        except Exception as e:
            print(f"⚠️ CrossRef search error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    @staticmethod
    def search_semantic_scholar(query: str, max_results: int = 20) -> List[Dict]:
        """Search Semantic Scholar API (free, no API key needed)"""
        results = []
        try:
            import urllib.request
            search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={max_results}&fields=title,authors,abstract,year,citationCount,url,doi"
            response = urllib.request.urlopen(search_url, timeout=10)
            data = response.read().decode('utf-8')
            
            import json as json_module
            response_data = json_module.loads(data)
            
            for paper in response_data.get('data', []):
                results.append({
                    'title': paper.get('title', 'N/A'),
                    'authors': ', '.join([a.get('name', '') for a in paper.get('authors', [])]) or 'Unknown',
                    'abstract': paper.get('abstract', '')[:500] or '',
                    'year': paper.get('year', 2024),
                    'doi': paper.get('doi', ''),
                    'url': paper.get('url', ''),
                    'citation_count': paper.get('citationCount', 0)
                })
        except Exception as e:
            print(f"⚠️ Semantic Scholar search error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    @staticmethod
    def log_search(user_id: int, query: str, sources: List[str], result_count: int):
        """Log search for analytics"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO search_logs (user_id, query, sources, result_count)
                VALUES (%s, %s, %s, %s)
            """, (user_id, query, json.dumps(sources), result_count))
