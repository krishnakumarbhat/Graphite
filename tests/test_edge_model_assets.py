from scripts.edge_models.workspace import ensure_edge_workspace
from scripts.verify_edge_models import verify_edge_workspace


def test_edge_model_workspace_assets_are_generated_and_valid() -> None:
  generated_paths = ensure_edge_workspace()
  verified_paths = verify_edge_workspace()

  assert generated_paths
  assert verified_paths