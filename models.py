from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class User:
    id: int
    email: str
    first_name: str
    last_name: str
    tier: str
    is_verified: bool
    created_at: str
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

@dataclass
class Paper:
    id: int
    title: str
    authors: str
    abstract: Optional[str]
    year: int
    source: str
    arxiv_id: Optional[str]
    doi: Optional[str]
    pdf_path: Optional[str]
    pdf_text: Optional[str]
    asip_funded: bool
    tags: List[str]
    citation_count: int
    added_by: Optional[int]
    created_at: str
    url: Optional[str] = None
    
    @staticmethod
    def from_db_row(row):
        """Convert database row to Paper object"""
        paper_dict = dict(row)
        try:
            paper_dict['tags'] = json.loads(paper_dict['tags']) if paper_dict.get('tags') else []
        except (json.JSONDecodeError, TypeError):
            # Fallback: treat as comma-separated string if it's a string, otherwise empty list
            tags_val = paper_dict.get('tags')
            if isinstance(tags_val, str):
                paper_dict['tags'] = [t.strip() for t in tags_val.split(',') if t.strip()]
            else:
                paper_dict['tags'] = []
        paper_dict['asip_funded'] = bool(paper_dict.get('asip_funded', False))
        return Paper(**paper_dict)
    
    def to_dict(self):
        """Convert Paper to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'year': self.year,
            'source': self.source,
            'arxiv_id': self.arxiv_id,
            'doi': self.doi,
            'asip_funded': self.asip_funded,
            'tags': self.tags,
            'citation_count': self.citation_count,
            'url': self.url,
            'bibtex': self.generate_bibtex()
        }
    
    def generate_bibtex(self):
        """Generate BibTeX citation"""
        first_author = self.authors.split(',')[0].strip().replace(' ', '')
        arxiv_id = f"arXiv:{self.arxiv_id}" if self.arxiv_id else ""
        doi_str = self.doi if self.doi else "N/A"
        
        return f"""@article{{{first_author}{self.year},
  title={{{self.title}}},
  author={{{self.authors}}},
  journal={{arXiv preprint {arxiv_id}}},
  year={{{self.year}}},
  doi={{{doi_str}}}
}}"""

@dataclass
class SearchResult:
    papers: List[Paper]
    total_count: int
    query: str
    sources_used: List[str]
    execution_time: float
