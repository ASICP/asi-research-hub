import re

with open('static/search.html', 'r') as f:
    content = f.read()

old_handle_upload = r'        async function handleUpload\(event\) \{.*?if \(!selectedFile\) return;.*?const formData = new FormData\(\);.*?formData\.append\(\'file\', selectedFile\);.*?const title = .*?const authors = .*?const year = .*?const abstract = .*?if \(title\) formData\.append\(\'title\', title\);.*?if \(authors\) formData\.append\(\'authors\', authors\);.*?if \(year\) formData\.append\(\'year\', year\);.*?if \(abstract\) formData\.append\(\'abstract\', abstract\);.*?const response = await fetch\(`\$\{API_URL\}/papers/upload`, \{.*?method: \'POST\',.*?headers: \{ \'Authorization\': `Bearer \$\{accessToken\}` \},.*?body: formData'

new_handle_upload = '''        async function handleUpload(event) {
            event.preventDefault();

            const paperUrl = document.getElementById('paper-url').value.trim();
            if (!paperUrl) {
                alert('Please provide a paper URL');
                return;
            }

            if (!accessToken) {
                alert('Please log in to upload papers');
                window.location.href = '/static/login.html';
                return;
            }

            const statusDiv = document.getElementById('upload-status');
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<div class="status-message">⏳ Validating URL and processing...</div>';

            const btn = document.getElementById('upload-btn');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Processing...';
            }

            const title = document.getElementById('upload-title').value.trim();
            const authors = document.getElementById('upload-authors').value.trim();
            const year = document.getElementById('upload-year').value;
            const abstract = document.getElementById('upload-abstract').value.trim();
            const tagsInput = document.getElementById('upload-tags').value.trim();

            const payload = { url: paperUrl };
            if (title) payload.title = title;
            if (authors) payload.authors = authors;
            if (year) payload.year = parseInt(year);
            if (abstract) payload.abstract = abstract;
            if (tagsInput) {
                payload.tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
            }

            try {
                const response = await fetch(`${API_URL}/papers/upload`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload'''

# Find and replace the handleUpload function
pattern = r'async function handleUpload\(event\) \{[^}]*?if \(!selectedFile\) return;.*?body: formData\s*\}'
replacement = new_handle_upload + '''
                });

                const result = await response.json();

                if (result.success) {
                    statusDiv.innerHTML = `<div class="status-message status-success">✅ ${result.message}</div>`;
                    setTimeout(() => {
                        closeUploadModal();
                    }, 2000);
                } else {
                    throw new Error(result.error || 'Upload failed');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status-message status-error">❌ ${error.message}</div>`;
                const btn = document.getElementById('upload-btn');
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Retry';
                }
            }
        }'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('static/search.html', 'w') as f:
    f.write(content)

print("handleUpload function updated!")