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

# Tag keywords mapping for auto-assignment
TAG_KEYWORDS = {
    'alignment': ['alignment', 'aligned', 'aligning'],
    'AI_safety': ['safety', 'safe', 'safer', 'safeguard'],
    'AI_risks': ['risk', 'risks', 'danger', 'dangerous', 'threat'],
    'interpretability': ['interpretability', 'interpretable', 'explainability', 'explainable', 'xai'],
    'reward_hacking': ['reward hacking', 'reward gaming', 'reward manipulation'],
    'robustness': ['robust', 'robustness', 'adversarial'],
    'value_alignment': ['value alignment', 'human values', 'value learning'],
    'corrigibility': ['corrigibility', 'corrigible', 'shutdown'],
    'mesa_optimization': ['mesa-optimization', 'mesa optimization', 'inner alignment'],
    'outer_alignment': ['outer alignment'],
    'training': ['training', 'train', 'fine-tuning', 'fine tuning', 'finetuning'],
    'RLHF': ['rlhf', 'reinforcement learning from human feedback', 'human feedback'],
    'constitutional_AI': ['constitutional ai', 'constitutional'],
    'deception': ['deception', 'deceptive', 'lying', 'dishonest'],
    'goal_misgeneralization': ['goal misgeneralization', 'distributional shift'],
    'scalable_oversight': ['scalable oversight', 'oversight'],
    'red_teaming': ['red team', 'red-team', 'adversarial testing'],
    'language_models': ['language model', 'llm', 'gpt', 'transformer', 'large language'],
    'neural_networks': ['neural network', 'deep learning', 'deep neural'],
    'machine_learning': ['machine learning', 'ml'],
    'AGI': ['agi', 'artificial general intelligence', 'general intelligence'],
    'superintelligence': ['superintelligence', 'superintelligent', 'super-intelligence'],
    'existential_risk': ['existential risk', 'x-risk', 'extinction'],
    'governance': ['governance', 'policy', 'regulation'],
    'ethics': ['ethics', 'ethical', 'moral'],
}

def assign_tags_from_text(title: str, abstract: str) -> List[str]:
    """Assign relevant AI safety tags based on title and abstract content"""
    text = (title + ' ' + abstract).lower()
    assigned_tags = []
    
    for tag, keywords in TAG_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                assigned_tags.append(tag)
                break
    
    return assigned_tags[:5]  # Limit to 5 most relevant tags

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
                params.append(str(year_from))
            
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
        
        print(f"🔍 Unified search - Query: {query}, Sources requested: {sources}")
        
        # Search internal database
        if 'internal' in sources:
            internal_results = SearchService.search_internal(
                query, tags, year_from, asip_funded_only
            )
            all_papers.extend(internal_results)
            sources_used.append('internal')
        
        # Google Scholar disabled - access blocked by Google
        # if 'scholar' in sources:
        #     scholar_results = SearchService.search_google_scholar(query)
        #     for result in scholar_results:
        #         paper = Paper(...)
        #         all_papers.append(paper)
        #     sources_used.append('Google Scholar')
        
        # Search arXiv
        if 'arxiv' in sources:
            print(f"🔍 Searching arXiv...")
            arxiv_results = SearchService.search_arxiv(query)
            print(f"✅ arXiv returned {len(arxiv_results)} results")
            for result in arxiv_results:
                # Auto-assign tags based on content
                auto_tags = assign_tags_from_text(result['title'], result['abstract'])
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
                    tags=auto_tags,
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
                # Auto-assign tags based on content
                auto_tags = assign_tags_from_text(result['title'], result['abstract'])
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
                    tags=auto_tags,
                    citation_count=0,
                    added_by=None,
                    created_at='',
                    url=result.get('url', '')
                )
                all_papers.append(paper)
            sources_used.append('CrossRef')
        
        # Search Semantic Scholar
        if 'semantic_scholar' in sources:
            print(f"🔍 Searching Semantic Scholar...")
            semantic_results = SearchService.search_semantic_scholar(query)
            print(f"✅ Semantic Scholar returned {len(semantic_results)} results")
            for result in semantic_results:
                # Auto-assign tags based on content
                auto_tags = assign_tags_from_text(result['title'], result['abstract'])
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
                    tags=auto_tags,
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
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text if title_elem is not None and title_elem.text else 'N/A'
                
                authors = []
                for a in entry.findall('{http://www.w3.org/2005/Atom}author'):
                    name_elem = a.find('{http://www.w3.org/2005/Atom}name')
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                
                abstract_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                abstract = abstract_elem.text.strip() if abstract_elem is not None and abstract_elem.text else ''
                
                id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                arxiv_id = id_elem.text.split('/abs/')[-1] if id_elem is not None and id_elem.text else 'N/A'
                
                pub_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                published = pub_elem.text[:4] if pub_elem is not None and pub_elem.text else '2024'
                
                results.append({
                    'title': title,
                    'authors': ', '.join(authors) if authors else 'Unknown',
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
            import urllib.request, urllib.parse, urllib.error
            import time
            
            search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={max_results}&fields=title,authors,abstract,year,citationCount,url"
            
            # Add proper headers to avoid rate limiting
            request = urllib.request.Request(
                search_url,
                headers={'User-Agent': 'ASI-Research-Hub/1.0 (+https://asi.org)'}
            )
            
            try:
                response = urllib.request.urlopen(request, timeout=10)
                data = response.read().decode('utf-8')
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    print(f"⚠️ Semantic Scholar rate limited (429). Waiting before retry...")
                    time.sleep(2)
                    response = urllib.request.urlopen(request, timeout=10)
                    data = response.read().decode('utf-8')
                else:
                    raise
            
            import json as json_module
            response_data = json_module.loads(data)
            
            # Check for error message in response
            if 'message' in response_data and 'Too Many Requests' in response_data.get('message', ''):
                print(f"⚠️ Semantic Scholar API error: {response_data['message']}")
                return results
            
            for paper in response_data.get('data', []):
                results.append({
                    'title': paper.get('title', 'N/A'),
                    'authors': ', '.join([a.get('name', '') for a in paper.get('authors', [])]) or 'Unknown',
                    'abstract': paper.get('abstract', '')[:500] or '',
                    'year': paper.get('year', 2024),
                    'doi': '',
                    'url': paper.get('url', ''),
                    'citation_count': paper.get('citationCount', 0)
                })
        except Exception as e:
            print(f"⚠️ Semantic Scholar search error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    # ============================================================================
    # Optional Helper Functions: Use cleaner libraries (feedparser, requests)
    # Keep stdlib versions as fallback in main search methods
    # ============================================================================
    
    @staticmethod
    def search_arxiv_helper(query: str, max_results: int = 20) -> List[Dict]:
        """Search arXiv using feedparser (cleaner alternative to stdlib XML parsing)"""
        results = []
        try:
            import feedparser
            search_url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
            feed = feedparser.parse(search_url)
            
            for entry in feed.entries:
                authors = [author.name for author in entry.get('authors', [])]
                arxiv_id = entry.id.split('/abs/')[-1] if 'id' in entry else 'N/A'
                
                results.append({
                    'title': entry.get('title', 'N/A'),
                    'authors': ', '.join(authors) if authors else 'Unknown',
                    'abstract': entry.get('summary', '')[:500],
                    'year': int(entry.get('published', '2024')[:4]),
                    'arxiv_id': arxiv_id,
                    'url': f'https://arxiv.org/abs/{arxiv_id}'
                })
        except Exception as e:
            print(f"⚠️ arXiv helper error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    @staticmethod
    def search_crossref_helper(query: str, max_results: int = 20) -> List[Dict]:
        """Search CrossRef using requests (cleaner alternative to stdlib urllib)"""
        results = []
        try:
            import requests
            search_url = f"https://api.crossref.org/works?query={query}&rows={max_results}&sort=published&order=desc"
            response = requests.get(search_url, timeout=10)
            data = response.json()
            
            for item in data.get('message', {}).get('items', []):
                authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() 
                          for a in item.get('author', [])]
                
                results.append({
                    'title': item.get('title', ['N/A'])[0] if item.get('title') else 'N/A',
                    'authors': ', '.join(authors) if authors else 'Unknown',
                    'abstract': item.get('abstract', '')[:500] or '',
                    'year': item.get('published-online', {}).get('date-parts', [[2024]])[0][0],
                    'doi': item.get('DOI', ''),
                    'url': item.get('URL', '')
                })
        except Exception as e:
            print(f"⚠️ CrossRef helper error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    @staticmethod
    def search_semantic_scholar_helper(query: str, max_results: int = 20) -> List[Dict]:
        """Search Semantic Scholar using requests (cleaner alternative to stdlib urllib)"""
        results = []
        try:
            import requests
            import time
            
            search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,authors,abstract,year,citationCount,url"
            headers = {'User-Agent': 'ASI-Research-Hub/1.0 (+https://asi.org)'}
            
            try:
                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    print(f"⚠️ Semantic Scholar rate limited (429). Waiting before retry...")
                    time.sleep(2)
                    response = requests.get(search_url, headers=headers, timeout=10)
                    response.raise_for_status()
                else:
                    raise
            
            data = response.json()
            
            # Check for error message in response
            if 'message' in data and 'Too Many Requests' in data.get('message', ''):
                print(f"⚠️ Semantic Scholar API error: {data['message']}")
                return results
            
            for paper in data.get('data', []):
                authors = [author.get('name', '') for author in paper.get('authors', [])]
                
                results.append({
                    'title': paper.get('title', 'N/A'),
                    'authors': ', '.join(authors) if authors else 'Unknown',
                    'abstract': paper.get('abstract', '')[:500] or '',
                    'year': paper.get('year', 2024),
                    'doi': '',
                    'url': paper.get('url', ''),
                    'citation_count': paper.get('citationCount', 0)
                })
        except Exception as e:
            print(f"⚠️ Semantic Scholar helper error: {type(e).__name__}: {str(e)[:100]}")
        return results
    
    # ============================================================================
    # End of Helper Functions
    # ============================================================================
    
    @staticmethod
    def log_search(user_id: int, query: str, sources: List[str], result_count: int):
        """Log search for analytics"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO search_logs (user_id, query, sources, result_count)
                VALUES (%s, %s, %s, %s)
            """, (user_id, query, json.dumps(sources), result_count))
