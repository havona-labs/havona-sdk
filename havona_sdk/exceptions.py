class HavonaError(Exception):
    """Base exception for all Havona SDK errors."""

    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self):
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.response_body:
            parts.append(f"— {self.response_body[:200]}")
        return " ".join(parts)


class AuthError(HavonaError):
    """Authentication failed — bad credentials, expired token, wrong audience."""


class BlockchainError(HavonaError):
    """Blockchain write failed or confirmation timed out."""


class ValidationError(HavonaError):
    """Request payload failed server-side validation."""


class NotFoundError(HavonaError):
    """Requested record does not exist."""


class GraphQLError(HavonaError):
    """GraphQL query returned errors."""

    def __init__(self, errors: list):
        messages = [e.get("message", str(e)) for e in errors]
        super().__init__(f"GraphQL errors: {messages}")
        self.errors = errors
