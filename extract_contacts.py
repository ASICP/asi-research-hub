#!/usr/bin/env python3
"""
Script to extract contact information (emails) from PDFs
Usage: python extract_contacts.py
"""

import os
import re
import csv
import PyPDF2
from database import get_db

def extract_emails(text):
    """Extract email addresses from text using regex"""
    # Basic email regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    
    # Filter out common false positives or junk
    valid_emails = []
    ignore_list = ['example.com', 'domain.com', 'email.com']
    
    for email in emails:
        email = email.lower()
        if any(ignore in email for ignore in ignore_list):
            continue
        # Remove trailing dots if picked up
        if email.endswith('.'):
            email = email[:-1]
        valid_emails.append(email)
        
    return list(set(valid_emails))  # Deduplicate

def main():
    upload_dir = 'static/uploads'
    output_file = 'contacts.csv'
    
    if not os.path.exists(upload_dir):
        print(f"❌ Directory {upload_dir} not found!")
        return
        
    print(f"🔍 Scanning PDFs in {upload_dir}...")
    
    results = []
    
    for filename in os.listdir(upload_dir):
        if not filename.lower().endswith('.pdf'):
            continue
            
        filepath = os.path.join(upload_dir, filename)
        print(f"📄 Processing {filename}...")
        
        try:
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                # Only scan first 2 pages for contacts (usually where they are)
                num_pages = min(len(reader.pages), 2)
                for i in range(num_pages):
                    text += reader.pages[i].extract_text()
            
            emails = extract_emails(text)
            
            if emails:
                print(f"   ✅ Found: {', '.join(emails)}")
                for email in emails:
                    results.append({
                        'Paper Filename': filename,
                        'Email': email,
                        'Source': 'PDF Extraction'
                    })
            else:
                print("   ⚠️  No emails found")
                
        except Exception as e:
            print(f"   ❌ Error reading PDF: {e}")
            
    # Write to CSV
    if results:
        fieldnames = ['Paper Filename', 'Email', 'Source']
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"\n✅ Extraction complete! Saved {len(results)} contacts to {output_file}")
    else:
        print("\n⚠️  No contacts found in any files.")

if __name__ == '__main__':
    main()
