
class HTTPLLMException(LLMBaseException):
    """Base exception class for HTTP-related LLM errors."""
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message, error_code)
        self.status_code = status_code

# 4xx Client Errors
class BadRequestError(HTTPLLMException):
    """400 - Bad Request: Invalid request format or parameters."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 400)

class UnauthorizedError(HTTPLLMException):
    """401 - Unauthorized: Missing or invalid authentication."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 401)

class ForbiddenError(HTTPLLMException):
    """403 - Forbidden: Valid credentials but insufficient permissions."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 403)

class NotFoundError(HTTPLLMException):
    """404 - Not Found: Requested resource or endpoint doesn't exist."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 404)

class MethodNotAllowedError(HTTPLLMException):
    """405 - Method Not Allowed: HTTP method not supported for endpoint."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 405)

class NotAcceptableError(HTTPLLMException):
    """406 - Not Acceptable: Requested content type not supported."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 406)

class ConflictError(HTTPLLMException):
    """409 - Conflict: Request conflicts with current state."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 409)

class PayloadTooLargeError(HTTPLLMException):
    """413 - Payload Too Large: Request payload exceeds size limits."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 413)

class UnsupportedMediaTypeError(HTTPLLMException):
    """415 - Unsupported Media Type: Content-Type not supported."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 415)

class UnprocessableEntityError(HTTPLLMException):
    """422 - Unprocessable Entity: Valid format but semantic errors."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 422)

class TooManyRequestsError(HTTPLLMException):
    """429 - Too Many Requests: Rate limit exceeded."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 429)

# 5xx Server Errors
class InternalServerError(HTTPLLMException):
    """500 - Internal Server Error: Unexpected server error."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 500)

class NotImplementedError(HTTPLLMException):
    """501 - Not Implemented: Functionality not implemented."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 501)

class BadGatewayError(HTTPLLMException):
    """502 - Bad Gateway: Upstream service error."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 502)

class ServiceUnavailableError(HTTPLLMException):
    """503 - Service Unavailable: Service temporarily unavailable."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 503)

class GatewayTimeoutError(HTTPLLMException):
    """504 - Gateway Timeout: Upstream service timeout."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 504)

class InsufficientStorageError(HTTPLLMException):
    """507 - Insufficient Storage: Server storage full."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code, 507)
