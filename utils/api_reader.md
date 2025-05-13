## Usage Example of GitHubAPIReader

```python
from api_reader import GitHubAPIReader

# Initialize with multiple tokens
tokens = [
    "ghp_abc123...",
    "ghp_def456...",
    "ghp_ghi789..."
]
reader = GitHubAPIReader(tokens=tokens)

# Make requests - will automatically rotate tokens as needed
url = "https://api.github.com/repos/octocat/Hello-World"
data, should_stop = reader.read_url(url)

if data:
    print(f"Repository description: {data['description']}")

# Check token usage stats
print("Token usage statistics:")
print(reader.get_usage_stats())
```


## Environment Variable Setup

You can also configure tokens via environment variable:

```bash
export GITHUB_TOKEN="ghp_abc123...,ghp_def456...,ghp_ghi789..."
```

Then initialize without explicit tokens:

```python
reader = GitHubAPIReader()  # Automatically uses tokens from GITHUB_TOKENS
```

Our implementation provides robust handling of GitHub API rate limits by efficiently utilizing multiple tokens when available.