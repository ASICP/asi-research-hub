import re

with open('static/search.html', 'r') as f:
    content = f.read()

old_upload_form = '''                    <!-- Drag and drop zone -->
                    <div id="drop-zone" class="drop-zone">
                        <div style="font-size: 48px; margin-bottom: 16px;">📄</div>
                        <p style="font-size: 16px; margin-bottom: 8px;">Drag and drop your PDF here</p>
                        <p style="font-size: 14px; color: var(--text-tertiary); margin-bottom: 16px;">or click to browse
                            (max 16MB)</p>
                        <input type="file" id="file-input" accept=".pdf" style="display: none;">
                        <button type="button" onclick="document.getElementById('file-input').click()"
                            style="width: auto; margin-top: 16px; padding: 10px 24px;">Browse Files</button>
                    </div>

                    <!-- File preview (hidden initially) -->
                    <div id="file-preview" style="display: none; margin-top: 20px;">
                        <div class="file-preview-card">
                            <div style="font-weight: 600; margin-bottom: 4px;" id="file-name"></div>
                            <div style="font-size: 13px; color: var(--text-secondary);" id="file-size"></div>
                        </div>
                    </div>

                    <!-- Optional metadata -->
                    <div id="metadata-fields" style="display: none; margin-top: 20px;">'''

new_upload_form = '''                    <!-- Public Link Input -->
                    <div class="input-group">
                        <label for="paper-url">Paper URL (required)</label>
                        <input type="url" id="paper-url" placeholder="https://example.com/paper.pdf" required
                               style="width: 100%; padding: 12px; background: var(--bg-tertiary);
                                      border: 1px solid var(--border-color); border-radius: 8px;
                                      color: var(--text-primary); font-size: 14px;">
                        <p style="font-size: 12px; color: var(--text-tertiary); margin-top: 8px;">
                            Provide a publicly accessible link to your paper (PDF format)
                        </p>
                    </div>

                    <!-- URL validation status -->
                    <div id="url-validation" style="display: none; margin-top: 12px; padding: 12px; border-radius: 8px;"></div>

                    <!-- Optional metadata -->
                    <div id="metadata-fields" style="margin-top: 20px;">'''

content = content.replace(old_upload_form, new_upload_form)

with open('static/search.html', 'w') as f:
    f.write(content)

print("Upload form updated to URL-based!")