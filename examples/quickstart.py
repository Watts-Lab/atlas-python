"""Quick start example for Atlas SDK."""

import os

from wattslab_atlas import AtlasClient


def main():
    """Simple example of using Atlas SDK."""

    api_key = os.environ.get("ATLAS_API_KEY") or input("Atlas API key: ").strip()
    client = AtlasClient(api_key=api_key)

    print("\n=== Features ===")
    features = client.list_features()
    print(f"Found {len(features)} features")
    for feature in features[:3]:
        print(f"  - {feature.feature_name}: {feature.feature_description}")

    print("\n=== Papers ===")
    papers = client.list_papers(page=1, page_size=5)
    print(f"Total papers: {papers.total_papers}")
    for paper in papers.papers:
        print(f"  - {paper.title or paper.file_name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
