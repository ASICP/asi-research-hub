#!/usr/bin/env python3
"""
Helper script to upload papers to the ASI Research Hub database
Usage: python upload_papers.py
"""

import PyPDF2
import json
import sys
from database import get_db, init_db
import os

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"❌ Error extracting text from {pdf_path}: {e}")
        return ""

def upload_paper(title, authors, year, abstract="", pdf_path=None, tags=None, 
                arxiv_id=None, doi=None, asip_funded=False, citation_count=0):
    """Upload a paper to the database"""
    
    if tags is None:
        tags = []
    
    # Extract PDF text if path provided
    pdf_text = ""
    if pdf_path and os.path.exists(pdf_path):
        pdf_text = extract_pdf_text(pdf_path)
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO papers 
                (title, authors, year, abstract, pdf_path, pdf_text, tags, 
                 arxiv_id, doi, asip_funded, citation_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, authors, year, abstract, pdf_path, pdf_text, 
                  json.dumps(tags), arxiv_id, doi, asip_funded, citation_count))
            
            paper_id = cursor.lastrowid
            print(f"✅ Uploaded: {title} (ID: {paper_id})")
            return paper_id
    except Exception as e:
        print(f"❌ Error uploading paper: {e}")
        return None

def upload_sample_papers():
    """Upload sample papers for testing"""
    
    print("📚 Uploading sample AI safety research papers...\n")
    
    # Sample papers from AI safety research
    papers = [
        {
            'title': 'Constitutional AI: Harmlessness from AI Feedback',
            'authors': 'Yuntao Bai, Saurav Kadavath, Sandipan Kundu, Amanda Askell',
            'year': 2022,
            'abstract': 'We develop a training method for AI systems to be harmless and helpful through constitutional principles.',
            'tags': ['alignment_fundamentals', 'technical_safety'],
            'arxiv_id': '2212.08073',
            'citation_count': 245,
            'asip_funded': False
        },
        {
            'title': 'Mechanistic Interpretability for AI Safety',
            'authors': 'Neel Nanda, Tom Lieberum, Chris Olah',
            'year': 2023,
            'abstract': 'We explore techniques for understanding neural network internals to improve AI safety.',
            'tags': ['interpretability', 'technical_safety'],
            'citation_count': 128,
            'asip_funded': True
        },
        {
            'title': 'Red Teaming Language Models with Language Models',
            'authors': 'Ethan Perez, Saffron Huang, Francis Song, Trevor Cai',
            'year': 2022,
            'abstract': 'We use language models to generate test cases that find failures in other language models.',
            'tags': ['red_teaming', 'robustness'],
            'arxiv_id': '2202.03286',
            'citation_count': 192,
            'asip_funded': False
        },
        {
            'title': 'AI Governance: Opportunity and Theory of Impact',
            'authors': 'Allan Dafoe',
            'year': 2021,
            'abstract': 'This paper outlines key challenges and opportunities in the governance of artificial intelligence.',
            'tags': ['governance', 'ethics'],
            'citation_count': 314,
            'asip_funded': False
        },
        {
            'title': 'Scalable Oversight of AI Systems via Recursive Reward Modeling',
            'authors': 'Jan Leike, David Krueger, Tom Everitt, Miljan Martic',
            'year': 2023,
            'abstract': 'We propose methods for humans to provide oversight of AI systems whose behavior they cannot directly evaluate.',
            'tags': ['alignment_fundamentals', 'technical_safety'],
            'citation_count': 87,
            'asip_funded': True
        },
        {
            'title': 'Adversarial Training for Free!',
            'authors': 'Ali Shafahi, Mahyar Najibi, Amin Ghiasi, Tom Goldstein',
            'year': 2019,
            'abstract': 'We introduce a method to perform adversarial training at no additional computational cost.',
            'tags': ['robustness', 'technical_safety'],
            'arxiv_id': '1904.12843',
            'citation_count': 521,
            'asip_funded': False
        },
        {
            'title': 'The Alignment Problem: Machine Learning and Human Values',
            'authors': 'Brian Christian',
            'year': 2020,
            'abstract': 'A comprehensive exploration of how to align AI systems with human values and intentions.',
            'tags': ['alignment_fundamentals', 'ethics'],
            'citation_count': 412,
            'asip_funded': False
        },
        {
            'title': 'Concrete Problems in AI Safety',
            'authors': 'Dario Amodei, Chris Olah, Jacob Steinhardt, Paul Christiano',
            'year': 2016,
            'abstract': 'We identify concrete technical problems that seem important for AI safety.',
            'tags': ['alignment_fundamentals', 'technical_safety'],
            'arxiv_id': '1606.06565',
            'citation_count': 1842,
            'asip_funded': False
        },
        {
            'title': 'Language Models as Agent Models',
            'authors': 'Jacob Andreas',
            'year': 2022,
            'abstract': 'We show how language models can be understood as models of rational agents.',
            'tags': ['interpretability', 'alignment_fundamentals'],
            'arxiv_id': '2212.01681',
            'citation_count': 156,
            'asip_funded': True
        },
        {
            'title': 'AI Safety Gridworlds',
            'authors': 'Jan Leike, Miljan Martic, Victoria Krakovna, Pedro Ortega',
            'year': 2017,
            'abstract': 'We present a suite of reinforcement learning environments to illustrate various safety properties.',
            'tags': ['technical_safety', 'robustness'],
            'arxiv_id': '1711.09883',
            'citation_count': 289,
        }
    ]
    
    # Upload each paper
    for paper in papers:
        upload_paper(**paper)
    
    print(f"\n✅ Successfully uploaded {len(papers)} sample papers!")
    print("🔍 You can now search for them in the Research Hub\n")

def load_papers_from_json(json_path='papers.json'):
    """Load papers from a JSON file"""
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return
        
    print(f"📂 Loading papers from {json_path}...")
    
    try:
        with open(json_path, 'r') as f:
            papers = json.load(f)
            
        count = 0
        for paper_data in papers:
            # Handle filename -> pdf_path mapping
            if 'filename' in paper_data and 'pdf_path' not in paper_data:
                paper_data['pdf_path'] = os.path.join('static/uploads', paper_data.pop('filename'))
            
            # Skip if PDF doesn't exist
            if 'pdf_path' in paper_data and not os.path.exists(paper_data['pdf_path']):
                print(f"⚠️  Skipping {paper_data.get('title', 'Unknown')}: File not found at {paper_data['pdf_path']}")
                continue
                
            upload_paper(**paper_data)
            count += 1
            
        print(f"\n✅ Successfully uploaded {count} papers from JSON!")
        
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in {json_path}")
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")

def main():
    """Main function"""
    # Initialize database if needed
    if not os.path.exists('asi_research_hub.db'):
        print("📦 Initializing database...")
        init_db()
        print()
    
    # Check for papers.json
    if os.path.exists('papers.json'):
        load_papers_from_json('papers.json')
    else:
        # Fallback to sample papers if no JSON provided
        print("ℹ️  No papers.json found. Uploading built-in sample papers...")
        upload_sample_papers()
    
    # Show stats
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM papers")
        total = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM papers WHERE asip_funded = TRUE")
        funded = cursor.fetchone()['count']
    
    print(f"📊 Database Statistics:")
    print(f"   Total papers: {total}")
    print(f"   ASIP-funded papers: {funded}")
    print(f"   Other papers: {total - funded}\n")

if __name__ == '__main__':
    main()
