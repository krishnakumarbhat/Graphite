from flask import Flask, jsonify, send_from_directory

from src.settings import Settings


def register_web_routes(app: Flask, settings: Settings) -> None:
  @app.get('/')
  def index():
    if not settings.frontend_build_dir.exists():
      return jsonify({'detail': 'Frontend build is not available.'}), 404
    return send_from_directory(settings.frontend_build_dir, 'index.html')

  @app.get('/<path:asset_path>')
  def serve_web_asset(asset_path: str):
    if asset_path.startswith('api/'):
      return jsonify({'detail': 'Not found.'}), 404

    if not settings.frontend_build_dir.exists():
      return jsonify({'detail': 'Frontend build is not available.'}), 404

    target_file = settings.frontend_build_dir / asset_path
    if target_file.is_file():
      return send_from_directory(settings.frontend_build_dir, asset_path)

    return send_from_directory(settings.frontend_build_dir, 'index.html')