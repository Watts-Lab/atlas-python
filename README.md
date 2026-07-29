# Atlas Python SDK

Official Python SDK for the Atlas API.

## Installation

```bash
pip install wattslab-atlas
```

## Quick Start

Create an Atlas API key in the web app, then pass it directly or set `ATLAS_API_KEY`.

```python
from wattslab_atlas import AtlasClient

client = AtlasClient(api_key="atlas_...")

features = client.list_features()
for feature in features:
    print(f"{feature.feature_name}: {feature.feature_description}")

papers = client.list_papers()
print(f"You have {papers.total_papers} papers")
```

You can also use an environment variable:

```bash
export ATLAS_API_KEY="atlas_..."
```

```python
from wattslab_atlas import AtlasClient

client = AtlasClient()
projects = client.list_projects()
```

## Authentication

API-key authentication is the recommended SDK path. The client sends the key as `X-API-Key` on every request.

```python
client = AtlasClient(api_key="atlas_...")
client.set_api_key("atlas_new_key")
```

The older magic-link flow is still available for compatibility:

```python
client = AtlasClient()
client.login("user@example.com")
client.validate_magic_link("token-from-email")
```

## Usage

**Working with Features**

```python
from wattslab_atlas.models import FeatureCreate

features = client.list_features()

feature = FeatureCreate(
    feature_name="Sample Size",
    feature_description="Number of participants",
    feature_identifier="sample_size",
    feature_prompt="Extract the total number of participants in the study.",
    feature_type="number",
)
created = client.create_feature(feature)

client.delete_feature(created.id)
```

**Choosing a model & provider for a project**

```python
from wattslab_atlas import AVAILABLE_MODELS

# See the curated model list per provider.
print(AVAILABLE_MODELS)
# {'atlas': ['gpt-5.4-mini', ...], 'openrouter': ['openai/gpt-5.4-mini',
#  'anthropic/claude-opus-4.8'], ...}

# Use Atlas' shared key (metered against your monthly budget) with the default model.
client.set_project_llm(project_id, provider="atlas")

# Or use your own OpenRouter key (billed by OpenRouter, not metered).
client.set_project_llm(
    project_id,
    provider="openrouter",
    model="anthropic/claude-opus-4.8",
)
```

Providers other than `atlas` require a saved key for that provider in
**Settings → Usage & Keys**. `model=None` uses the provider's default.

**Working with Papers**

```python
papers = client.list_papers(page=1, page_size=10)

result = client.upload_paper(
    project_id="project-123",
    file_path="paper.pdf",
)
task_id = result["paper.pdf"]

status = client.check_task_status(task_id)
client.reprocess_paper(paper_id, project_id)
```

**Managing Projects**

```python
features = client.get_project_features(project_id)

client.update_project_features(
    project_id,
    feature_ids=["feat1", "feat2"],
)

client.remove_project_features(
    project_id,
    feature_ids=["feat1"],
)

result = client.reprocess_project(project_id)
```

**Error Handling**

```python
from wattslab_atlas import AtlasClient, APIError, ResourceNotFoundError

client = AtlasClient(api_key="atlas_...")

try:
    features = client.list_features()
except APIError as exc:
    print(f"Atlas API error: {exc}")
except ResourceNotFoundError as exc:
    print(f"Resource not found: {exc}")
```

## Requirements

- Python 3.9+
- Atlas API key

