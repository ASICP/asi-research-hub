#!/usr/bin/env python3
"""
Script to download papers listed in papers.json
Usage: python download_papers.py
"""

import json
import os
import requests
import time
import sys

def download_file(url, filepath):
    """Download a file from a URL to a local path"""
    try:
        print(f"⬇️  Downloading from {url}...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

def main():
    json_path = 'papers.json'
    upload_dir = 'static/uploads'
    
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found!")
        return
        
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        with open(json_path, 'r') as f:
            papers = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return

    print(f"🔍 Found {len(papers)} papers in metadata.")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for paper in papers:
        filename = paper.get('filename')
        title = paper.get('title', 'Unknown Title')
        
        if not filename:
            print(f"⚠️  Skipping paper '{title}': No filename specified")
            fail_count += 1
            continue
            
        filepath = os.path.join(upload_dir, filename)
        
        # Check if already exists
        if os.path.exists(filepath):
            print(f"⏭️  Skipping '{title}': File already exists ({filename})")
            skip_count += 1
            continue
            
        print(f"\n📄 Processing: {title}")
        
        # Try ArXiv first
        arxiv_id = paper.get('arxiv_id')
        pdf_url = paper.get('pdf_url')
        
        downloaded = False
        
        if arxiv_id:
            # Clean ID (remove version if needed, though arxiv supports it)
            url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            if download_file(url, filepath):
                downloaded = True
                # Be nice to ArXiv API
                time.sleep(3)
        
        # Try direct URL if ArXiv failed or not present
        if not downloaded and pdf_url:
            if download_file(pdf_url, filepath):
                downloaded = True
        
        if downloaded:
            success_count += 1
        else:
            print(f"❌ Failed to download '{title}': No valid ArXiv ID or PDF URL provided")
            fail_count += 1
            
    print(f"\n==================================================")
    print(f"SUMMARY")
    print(f"==================================================")
    print(f"✅ Downloaded: {success_count}")
    print(f"⏭️  Skipped (Exists): {skip_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"==================================================")

if __name__ == '__main__':
    main()
