import re

with open('static/search.html', 'r') as f:
      content = f.read()
# 1. Add Google button after Upload Paper button (line ~795)
content = content.replace(
      '<button class="header-btn" onclick="openUploadModal()" title="Upload Paper">📄</button>',
      '''<button class="header-btn" onclick="openUploadModal()" title="Upload Paper">📄</button>
                  <button class="header-btn google-btn" onclick="window.open('https://notebooklm.google.com/', '_blank')" title="Open NotebookLM">
                      <div style="width: 24px; height: 24px; background: #4285f4; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 14px;">G</div>
                  </button>'''
  )

# 2. Remove old NotebookLM CSS (lines 759-775)
content = re.sub(
      r'        \.notebook-lm-link \{[^}]+\}',
      '        .google-btn {\n            background: transparent;\n            border: none;\n            padding: 0;\n            cursor: pointer;\n            transition: transform 0.2s;\n        }\n\n        .google-btn:hover {\n            transform: translateY(-2px);\n        }',
      content
  )
# 3. Remove old NotebookLM sections from metrics box (lines 871-891)
content = re.sub(
      r'                <!-- NotebookLM for Gmail users -->.*?</div>\s*</div>',
      '</div>',
      content,
      flags=re.DOTALL
  )

print("Changes applied! Review the file and save.")
with open('static/search.html', 'w') as f:
      f.write(content)
