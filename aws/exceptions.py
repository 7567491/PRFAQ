"""
Custom exceptions for AWS Marketplace integration
"""
from typing import Optional

class AWSError(Exception):
    """Base exception for AWS related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ConfigError(AWSError):
    """Configuration related errors"""
    pass

class AuthenticationError(AWSError):
    """Authentication related errors"""
    pass

class MarketplaceError(AWSError):
    """AWS Marketplace specific errors"""
    pass

class EntitlementError(MarketplaceError):
    """Entitlement verification errors"""
    pass

class SubscriptionError(MarketplaceError):
    """Subscription related errors"""
    pass 