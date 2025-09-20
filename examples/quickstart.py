"""Quick start example for Atlas SDK."""

from wattslab_atlas import AtlasClient
from wattslab_atlas.models import FeatureCreate


def main():
    """Simple example of using Atlas SDK."""

    # Initialize client (will auto-save tokens for future use)
    client = AtlasClient()

    # Login - will use saved token if available
    print("=== Authentication ===")
    result = client.login("user@example.com")

    # If a new login is needed, validate the magic link
    if "Check your email" in str(result.get("message", "")):
        token = input("Enter the magic link token from your email: ")
        client.validate_magic_link(token)

    # List features
    print("\n=== Features ===")
    features = client.list_features()
    print(f"Found {len(features)} features")
    for feature in features[:3]:  # Show first 3
        print(f"  • {feature.feature_name}: {feature.feature_description}")

    # Create a new feature
    print("\n=== Creating Feature ===")
    new_feature = FeatureCreate(
        feature_name="Sample Size",
        feature_description="Number of participants in the study",
        feature_identifier="sample_size",
        feature_type="integer",
    )
    created = client.create_feature(new_feature)
    print(f"Created: {created.feature_name} (ID: {created.id})")

    # List papers
    print("\n=== Papers ===")
    papers = client.list_papers(page=1, page_size=5)
    print(f"Total papers: {papers.total_papers}")
    for paper in papers.papers:
        print(f"  • {paper.title or paper.file_name}")

    # Upload a paper (example)
    # result = client.upload_paper("project-id", "paper.pdf")
    # print(f"Upload started: {result}")

    print("\n✓ All done!")


if __name__ == "__main__":
    main()
