import signal

from flask import Flask, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from src.errors import GraphiteError
from src.logging_config import configure_logging
from src.routes import build_api_blueprint
from src.services import ServiceRegistry
from src.settings import Settings, get_settings
from src.web_routes import register_web_routes


def _register_error_handlers(app: Flask) -> None:
  @app.errorhandler(GraphiteError)
  def handle_graphite_error(error: GraphiteError):
    return jsonify({'detail': str(error)}), error.status_code

  @app.errorhandler(ValidationError)
  def handle_validation_error(error: ValidationError):
    return (
      jsonify({'detail': 'Invalid request payload.', 'errors': error.errors(include_url=False)}),
      422,
    )

  @app.errorhandler(HTTPException)
  def handle_http_exception(error: HTTPException):
    return jsonify({'detail': error.description}), error.code or 500

  @app.errorhandler(Exception)
  def handle_unexpected_error(error: Exception):
    app.logger.exception('Unhandled application error: %s', error)
    return jsonify({'detail': 'Internal server error.'}), 500


def _register_cors(app: Flask, settings: Settings) -> None:
  @app.after_request
  def add_cors_headers(response):
    origin = request.headers.get('Origin', '').strip()
    if '*' in settings.cors_origin_list:
      response.headers['Access-Control-Allow-Origin'] = '*'
    elif origin and origin in settings.cors_origin_list:
      response.headers['Access-Control-Allow-Origin'] = origin
      response.headers['Vary'] = 'Origin'

    if response.headers.get('Access-Control-Allow-Origin') and settings.allow_credentials:
      response.headers['Access-Control-Allow-Credentials'] = 'true'

    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response


def _register_shutdown_handlers(services: ServiceRegistry, app: Flask) -> None:
  def shutdown_handler(signum: int, _frame) -> None:
    app.logger.info('Received shutdown signal %s. Closing backend services.', signum)
    services.close()

  for current_signal in (signal.SIGINT, signal.SIGTERM):
    try:
      signal.signal(current_signal, shutdown_handler)
    except ValueError:
      app.logger.debug('Skipping shutdown handler registration outside the main thread.')


def create_app(settings: Settings | None = None) -> Flask:
  resolved_settings = settings or get_settings()
  logger = configure_logging()
  services = ServiceRegistry(resolved_settings, logger)

  app = Flask(__name__, static_folder=None)
  app.config['JSON_SORT_KEYS'] = False
  app.register_blueprint(build_api_blueprint(services))
  _register_error_handlers(app)
  _register_cors(app, resolved_settings)
  _register_shutdown_handlers(services, app)
  register_web_routes(app, resolved_settings)

  return app