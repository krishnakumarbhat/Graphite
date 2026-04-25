from src.app_factory import create_app
from src.settings import get_settings

app = create_app()


if __name__ == '__main__':
  settings = get_settings()
  app.run(host='0.0.0.0', port=settings.graphite_port, debug=settings.flask_debug)
