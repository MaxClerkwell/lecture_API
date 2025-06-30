from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from authlib.integrations.requests_client import OAuth2Session
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Get settings once during module initialization

# OAuth2 configuration
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://keycloak.gruppe.ai/realms/demo/protocol/openid-connect/auth",
    tokenUrl=f"https://keycloak.gruppe.ai/realms/demo/protocol/openid-connect/token",
)




class KeycloakAuth:
    """Handles Keycloak authentication and token validation"""

    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID', 'demo-api')
        self.client_secret = os.getenv('CLIENT_SECRET', 'censored')
        self.keycloak_url = os.getenv('KEYCLOAK_URL', 'https://keycloak.gruppe.ai/auth/')
        self.realm = os.getenv('REALM', 'AI-Gruppe')
        self.required_role = "demo-api-role"

    async def get_token_data(self, token: str) -> Dict[str, Any]:
        """Introspect the token and return its data"""
        auth_session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        try:
            introspect_url = f"{self.keycloak_url}realms/{self.realm}/protocol/openid-connect/token/introspect"
            result = auth_session.introspect_token(
                url=introspect_url,
                token=token
            )

            if not result.ok:
                logger.error(f"Token introspection failed: {result.status_code} - {result.content}")
                raise HTTPException(status_code=401, detail="Failed to validate token")

            return result.json()
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    async def validate_token(self, token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
        """
        Validates the Keycloak token from the request's Authorization header.

        Args:
            token: The OAuth2 token from the request

        Returns:
            Dict: Token information when valid

        Raises:
            HTTPException: When token is invalid or user lacks required permissions
        """
        token_info = await self.get_token_data(token)

        if not token_info.get("active", False):
            raise HTTPException(status_code=401, detail="Token is invalid or expired")

        # Check for required role
        roles = token_info.get("realm_access", {}).get("roles", [])
        if self.required_role not in roles:
            logger.warning(f"User lacks required role '{self.required_role}'. Roles: {roles}")
            raise HTTPException(status_code=403, detail=f"User does not have the required role: {self.required_role}")

        return token_info


# Create a singleton instance for reuse
keycloak_auth = KeycloakAuth()


# Dependency for FastAPI routes
async def validate_keycloak_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency that validates a Keycloak token and returns the token info"""
    return await keycloak_auth.validate_token(token)
