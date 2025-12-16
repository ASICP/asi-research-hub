"""
Error handling for ARA v2.
Defines custom exceptions and error handlers for consistent API responses.
"""

from flask import jsonify


class ARAError(Exception):
    """Base exception for ARA v2."""

    def __init__(self, message: str, code: str = None, details: dict = None, status_code: int = 500):
        self.message = message
        self.code = code or 'INTERNAL_ERROR'
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


# Authentication Errors
class AuthenticationError(ARAError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code='AUTH_ERROR', status_code=401)


class AuthorizationError(ARAError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, code='AUTHZ_ERROR', status_code=403)


# API Errors
class BudgetExceededError(ARAError):
    """API budget exhausted."""

    def __init__(self, message: str = "API budget exhausted"):
        super().__init__(message, code='BUDGET_EXCEEDED', status_code=429)


class RateLimitError(ARAError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code='RATE_LIMIT', status_code=429)


# Data Errors
class PaperNotFoundError(ARAError):
    """Paper not found."""

    def __init__(self, paper_id: int):
        super().__init__(
            f"Paper {paper_id} not found",
            code='NOT_FOUND',
            status_code=404
        )


class ValidationError(ARAError):
    """Validation error."""

    def __init__(self, message: str, field: str = None):
        super().__init__(
            message,
            code='VALIDATION_ERROR',
            details={'field': field} if field else {},
            status_code=400
        )


# External Service Errors
class ExternalServiceError(ARAError):
    """External service error."""

    def __init__(self, service: str, message: str):
        super().__init__(
            f"{service} error: {message}",
            code='EXTERNAL_SERVICE_ERROR',
            details={'service': service},
            status_code=502
        )


def register_error_handlers(app):
    """
    Register error handlers with Flask app.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(ARAError)
    def handle_ara_error(error):
        """Handle custom ARA errors."""
        response = {
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            }
        }
        return jsonify(response), error.status_code

    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle 404 errors."""
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Endpoint not found'
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handle 405 errors."""
        return jsonify({
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'Method not allowed'
            }
        }), 405

    @app.errorhandler(500)
    def handle_internal_error(e):
        """Handle 500 errors."""
        app.logger.exception("Internal server error")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Handle any unexpected errors."""
        app.logger.exception(f"Unexpected error: {e}")
        return jsonify({
            'error': {
                'code': 'UNEXPECTED_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500

    app.logger.info("Error handlers registered")
