class GraphiteError(Exception):
  status_code = 500

  def __init__(self, message: str, status_code: int | None = None) -> None:
    super().__init__(message)
    if status_code is not None:
      self.status_code = status_code


class ConfigurationError(GraphiteError):
  status_code = 400


class UpstreamServiceError(GraphiteError):
  status_code = 502