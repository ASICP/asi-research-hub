import re

with open('static/search.html', 'r') as f:
            content = f.read()

# Remove old JavaScript functions (setupDragAndDrop, handleFile)
content = re.sub(
r'        function setupDragAndDrop\(\).*?        }',
'',
content,
flags=re.DOTALL
)

content = re.sub(
r'        function handleFile\(file\).*?        }',
'',
content,
flags=re.DOTALL
)

# Update closeUploadModal
old_close = '''        function closeUploadModal() {
            document.getElementById('upload-modal').style.display = 'none';
            selectedFile = null;
            document.getElementById('upload-form').reset();
            document.getElementById('drop-zone').style.display = 'block';
            document.getElementById('file-preview').style.display = 'none';
            document.getElementById('metadata-fields').style.display = 'none';
            if(document.getElementById('upload-btn')) document.getElementById('upload-btn').disabled = true;
            document.getElementById('upload-status').style.display = 'none';
        }'''

new_close = '''        function closeUploadModal() {
            document.getElementById('upload-modal').style.display = 'none';
            document.getElementById('upload-form').reset();
            document.getElementById('url-validation').style.display = 'none';
            document.getElementById('upload-status').style.display = 'none';
        }'''

content = content.replace(old_close, new_close)

# Update openUploadModal
content = content.replace(
'            setupDragAndDrop();',
''
)

# Remove selectedFile variable
content = content.replace('let selectedFile = null;', '')

with open('static/search.html', 'w') as f:
            f.write(content)

print("JavaScript updated for URL upload!")