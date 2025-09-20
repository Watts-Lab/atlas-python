# Atlas Python SDK

Official Python SDK for the Atlas API

## Installation

```bash
pip install wattslab-atlas
```

## Quick Start

```python
from wattslab_atlas import AtlasClient

# Initialize (auto-saves tokens for reuse)
client = AtlasClient()

# Login - uses saved token if available
client.login("your-email@example.com")

# First time? Validate the magic link from your email
# client.validate_magic_link("token-from-email")

# List features
features = client.list_features()
for f in features:
    print(f"{f.feature_name}: {f.feature_description}")

# List papers
papers = client.list_papers()
print(f"You have {papers.total_papers} papers")

```

## Authentication

Atlas uses magic link authentication with automatic token storage:

**First Time Setup**

```python
client = AtlasClient()

# Request magic link
client.login("user@example.com")
# >>> 📧 Magic link sent to user@example.com

# Check your email and validate
client.validate_magic_link("token-from-email")
# >>> ✓ Authentication successful! Token saved for future use.
```

**Subsequent Logins**

```python
# Tokens are automatically reused
client = AtlasClient()
client.login("user@example.com")
# >>> ✓ Using stored credentials for user@example.com
```

**Manual Token Management**

```python
# Disable auto-save if needed
client = AtlasClient(auto_save_token=False)

# Clear stored credentials
client.logout()
# >>> 🗑️ Cleared stored credentials.
```

## Usage

**Working with Features**

```python
from wattslab_atlas.models import FeatureCreate

# List all features
features = client.list_features()

# Create a feature
feature = FeatureCreate(
    feature_name="Sample Size",
    feature_description="Number of participants",
    feature_identifier="sample_size",
    feature_type="integer"
)
created = client.create_feature(feature)

# Delete a feature
client.delete_feature(feature_id)
```

**Working with Papers**

```python
# List papers with pagination
papers = client.list_papers(page=1, page_size=10)

# Upload a paper
result = client.upload_paper(
    project_id="project-123",
    file_path="paper.pdf"
)
task_id = result['paper.pdf']

# Check upload status
status = client.check_task_status(task_id)

# Reprocess a paper
client.reprocess_paper(paper_id, project_id)
```

**Managing Projects**

```python
# Get project features
features = client.get_project_features(project_id)

# Update project features
client.update_project_features(
    project_id,
    feature_ids=["feat1", "feat2"]
)

# Remove features from project
client.remove_project_features(
    project_id,
    feature_ids=["feat1"]
)

# Reprocess all papers in project
result = client.reprocess_project(project_id)
print(f"Reprocessing {result['total_papers']} papers")
```

**Error Handling**

```python
from wattslab_atlas import AtlasClient, AuthenticationError, ResourceNotFoundError

client = AtlasClient()

try:
    features = client.list_features()
except AuthenticationError:
    print("Please login first")
    client.login("user@example.com")
except ResourceNotFoundError as e:
    print(f"Resource not found: {e}")
```

## Requirements

- Python 3.8+
- Works in Jupyter notebooks
- Works in regular Python scripts

