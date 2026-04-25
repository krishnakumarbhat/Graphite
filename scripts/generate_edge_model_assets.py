import logging

from scripts.edge_models.workspace import ensure_edge_workspace


def main() -> int:
  logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
  created_paths = ensure_edge_workspace()
  logger = logging.getLogger('graphite.edge_models')
  logger.info('Prepared %s edge-model assets.', len(created_paths))
  return 0


if __name__ == '__main__':
  raise SystemExit(main())