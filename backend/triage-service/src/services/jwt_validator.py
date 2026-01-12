"""
JWT Claim Validation Logic
Elite Implementation Standard v2.0.0

Validates JWT claims (exp, sub, role) as defense-in-depth.
Typically Kong handles this, but we validate again for Zero-Trust.
"""

import time
import base64
import json
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

from models.errors import AuthenticationError, AuthorizationError


@dataclass
class JWTValidationResult:
    """Result of JWT validation"""
    valid: bool
    claims: Dict
    errors: List[str]
    warnings: List[str]


class JWTValidator:
    """
    Comprehensive JWT validator for Zero-Trust architecture

    Even though Kong validates JWTs at the edge, we re-validate
    in the service for defense-in-depth and audit logging.
    """

    def __init__(self):
        # Expected claims and their validation rules
        self.required_claims = {
            "sub": self._validate_sub_claim,
            "exp": self._validate_exp_claim,
            "role": self._validate_role_claim,
            "iat": self._validate_iat_claim
        }

        # Optional but recommended claims
        self.recommended_claims = ["iss", "aud", "jti"]

        # Valid role values
        self.valid_roles = ["student", "admin", "instructor"]

        # Token age limits (prevent very old tokens)
        self.max_token_age_seconds = 86400 * 7  # 7 days

    def validate_from_header(self, jwt_claims_header: str) -> JWTValidationResult:
        """
        Validate JWT claims from Kong's X-JWT-Claims header

        Args:
            jwt_claims_header: Base64 encoded JSON from Kong

        Returns:
            JWTValidationResult with validation status and details
        """
        try:
            # Decode base64 header
            claims_json = base64.b64decode(jwt_claims_header).decode('utf-8')
            claims = json.loads(claims_json)
        except Exception as e:
            return JWTValidationResult(
                valid=False,
                claims={},
                errors=[f"Failed to decode claims header: {str(e)}"],
                warnings=[]
            )

        return self.validate_claims(claims)

    def validate_claims(self, claims: Dict) -> JWTValidationResult:
        """
        Validate all JWT claims

        Args:
            claims: Decoded JWT claims dictionary

        Returns:
            Validation result with errors/warnings
        """
        errors = []
        warnings = []

        # 1. Validate required claims
        for claim_name, validator in self.required_claims.items():
            if claim_name not in claims:
                errors.append(f"Missing required claim: {claim_name}")
            else:
                try:
                    validator(claims[claim_name], claims)
                except Exception as e:
                    errors.append(f"Invalid {claim_name}: {str(e)}")

        # 2. Check for recommended claims
        for claim_name in self.recommended_claims:
            if claim_name not in claims:
                warnings.append(f"Missing recommended claim: {claim_name}")

        # 3. Validate claim relationships
        try:
            self._validate_claim_relationships(claims)
        except Exception as e:
            errors.append(f"Claim relationship validation failed: {str(e)}")

        # 4. Check token age
        try:
            self._validate_token_age(claims)
        except Exception as e:
            warnings.append(f"Token age warning: {str(e)}")

        is_valid = len(errors) == 0

        return JWTValidationResult(
            valid=is_valid,
            claims=claims,
            errors=errors,
            warnings=warnings
        )

    def _validate_sub_claim(self, sub: str, claims: Dict):
        """Validate subject claim (student_id)"""
        if not sub or not isinstance(sub, str):
            raise ValueError("Subject must be a non-empty string")

        if len(sub) < 3 or len(sub) > 100:
            raise ValueError("Subject length invalid (3-100 chars)")

        # Format check: should look like student-UUID or similar
        if not any(prefix in sub.lower() for prefix in ["student", "user", "instructor"]):
            warnings = ["Subject format unusual, expected 'student-xxx' pattern"]
            # This is a warning, not an error - for audit

    def _validate_exp_claim(self, exp: int, claims: Dict):
        """Validate expiration claim"""
        now = int(time.time())

        if not isinstance(exp, int):
            raise ValueError("Expiration must be integer timestamp")

        if exp < now:
            raise ValueError(f"Token expired at {datetime.fromtimestamp(exp)}")

        # Check if exp is too far in future (suspicious)
        max_exp = now + (86400 * 30)  # Max 30 days
        if exp > max_exp:
            raise ValueError("Expiration too far in future")

    def _validate_role_claim(self, role: str, claims: Dict):
        """Validate role claim"""
        if not role or not isinstance(role, str):
            raise ValueError("Role must be a non-empty string")

        if role not in self.valid_roles:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(self.valid_roles)}")

    def _validate_iat_claim(self, iat: int, claims: Dict):
        """Validate issued at claim"""
        now = int(time.time())

        if not isinstance(iat, int):
            raise ValueError("Issued-at must be integer timestamp")

        if iat > now:
            raise ValueError("Token issued in future")

        # Check for clock skew tolerance
        skew_limit = 300  # 5 minutes
        if now - iat > skew_limit:
            # This is normal for expired tokens, handled by exp check
            pass

    def _validate_claim_relationships(self, claims: Dict):
        """Validate relationships between claims"""
        # exp must be > iat
        if "exp" in claims and "iat" in claims:
            if claims["exp"] <= claims["iat"]:
                raise ValueError("Expiration must be after issued-at")

        # Check for reasonable time window
        if "exp" in claims and "iat" in claims:
            token_lifetime = claims["exp"] - claims["iat"]
            if token_lifetime < 60:  # Less than 1 minute
                warnings.append("Very short token lifetime")
            elif token_lifetime > 86400 * 30:  # More than 30 days
                warnings.append("Very long token lifetime")

    def _validate_token_age(self, claims: Dict):
        """Check token age against limits"""
        if "iat" in claims:
            age = int(time.time()) - claims["iat"]
            if age > self.max_token_age_seconds:
                raise ValueError(f"Token too old: {age/86400:.1f} days (max: 7 days)")

    def is_token_expired(self, claims: Dict) -> bool:
        """Quick check if token is expired"""
        if "exp" not in claims:
            return False
        return claims["exp"] < int(time.time())

    def get_token_expiry_info(self, claims: Dict) -> Dict:
        """Get detailed expiry information"""
        if "exp" not in claims:
            return {"status": "no_expiry"}

        now = int(time.time())
        exp = claims["exp"]
        remaining = exp - now

        if remaining <= 0:
            status = "expired"
        elif remaining < 3600:  # Less than 1 hour
            status = "expires_soon"
        else:
            status = "valid"

        return {
            "status": status,
            "expires_at": exp,
            "expires_in_seconds": remaining,
            "expires_in_human": self._format_duration(remaining),
            "formatted": datetime.fromtimestamp(exp).isoformat()
        }

    def _format_duration(self, seconds: int) -> str:
        """Format seconds into human readable duration"""
        if seconds < 0:
            return "expired"

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")

        return " ".join(parts) or "less than 1 minute"

    def extract_permissions(self, claims: Dict) -> Dict:
        """Extract permissions from claims"""
        permissions = {
            "role": claims.get("role"),
            "scopes": claims.get("scope", "").split(),
            "capabilities": []
        }

        # Map role to capabilities
        role = claims.get("role")
        if role == "student":
            permissions["capabilities"] = ["triage:read", "progress:read"]
        elif role == "instructor":
            permissions["capabilities"] = ["triage:read", "progress:read", "students:read"]
        elif role == "admin":
            permissions["capabilities"] = ["triage:read", "triage:write", "students:read", "students:write"]

        return permissions


# Global validator instance
jwt_validator = JWTValidator()


def validate_jwt_claims(claims_header: str) -> JWTValidationResult:
    """Convenience function for JWT validation"""
    return jwt_validator.validate_from_header(claims_header)


def validate_jwt_claims_dict(claims: Dict) -> JWTValidationResult:
    """Validate claims dictionary directly"""
    return jwt_validator.validate_claims(claims)


if __name__ == "__main__":
    # Test JWT validation
    print("=== JWT Validator Test ===")

    # Test case 1: Valid claims
    valid_claims = {
        "sub": "student-12345",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()) - 100,
        "role": "student",
        "iss": "learnflow-auth",
        "aud": "learnflow-services"
    }

    result = jwt_validator.validate_claims(valid_claims)
    print(f"Valid claims: {result.valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Permissions: {jwt_validator.extract_permissions(valid_claims)}")

    # Test case 2: Expired token
    expired_claims = {
        "sub": "student-12345",
        "exp": int(time.time()) - 100,
        "iat": int(time.time()) - 3600,
        "role": "student"
    }

    result = jwt_validator.validate_claims(expired_claims)
    print(f"\nExpired claims: {result.valid}")
    print(f"Errors: {result.errors}")

    # Test case 3: Missing required claim
    invalid_claims = {
        "sub": "student-12345",
        "exp": int(time.time()) + 3600
        # Missing "role"
    }

    result = jwt_validator.validate_claims(invalid_claims)
    print(f"\nMissing claim: {result.valid}")
    print(f"Errors: {result.errors}")

    # Test expiry info
    print(f"\nExpiry info: {jwt_validator.get_token_expiry_info(valid_claims)}")