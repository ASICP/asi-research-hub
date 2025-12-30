  import re
  with open('static/search.html', 'r') as f:
      content = f.read()

  match = re.search(r'async function handleUpload\(event\)', content)
  if match:
      start = match.start()
      lines = content[start:start+3000]
      print("=== handleUpload function ===")
      print(lines)
