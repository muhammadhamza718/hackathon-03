"""
Authorization Middleware - Permission Validation
Elite Implementation Standard v2.0.0

Validates student permissions for triage access.
Implements role-based access control (RBAC).
"""

from fastapi import Request, HTTPException, status
from typing import Dict, List, Optional
from dataclasses import dataclass

from models.errors import AuthorizationError


@dataclass
class Permission:
    """Permission definition"""
    resource: str
    action: str  # read, write, delete, etc.
    scope: Optional[str] = None  # Optional scope restriction


class AuthorizationMiddleware:
    """
    Role-Based Access Control (RBAC) for triage service

    Permission Matrix:
    - student: triage:read, progress:read
    - instructor: triage:read, progress:read, students:read
    - admin: triage:read, triage:write, students:read, students:write
    """

    def __init__(self):
        # Role to permission mapping
        self.role_permissions = {
            "student": [
                Permission("triage", "read"),
                Permission("progress", "read"),
                Permission("queries", "read"),
            ],
            "instructor": [
                Permission("triage", "read"),
                Permission("progress", "read"),
                Permission("students", "read"),
                Permission("analytics", "read"),
            ],
            "admin": [
                Permission("triage", "read"),
                Permission("triage", "write"),
                Permission("students", "read"),
                Permission("students", "write"),
                Permission("analytics", "read"),
                Permission("config", "read"),
                Permission("config", "write"),
            ]
        }

    def check_permission(self, security_context: Dict, required_permission: Permission) -> bool:
        """
        Check if user has required permission

        Args:
            security_context: From auth middleware
            required_permission: Permission required for operation

        Returns:
            bool: True if permission granted
        """
        role = security_context.get("role")
        if not role:
            return False

        if role not in self.role_permissions:
            return False

        user_permissions = self.role_permissions[role]

        # Check exact permission match
        for perm in user_permissions:
            if (perm.resource == required_permission.resource and
                perm.action == required_permission.action):
                # If scope is specified, it must match
                if required_permission.scope is None or perm.scope == required_permission.scope:
                    return True

        return False

    def verify_triage_access(self, security_context: Dict, student_id_in_path: Optional[str] = None) -> Dict:
        """
        Verify access to triage service

        Args:
            security_context: User's security context
            student_id_in_path: Optional student ID from URL path

        Returns:
            Dict with access decision and metadata

        Raises:
            AuthorizationError: If access denied
        """
        role = security_context.get("role")
        user_student_id = security_context.get("student_id")

        # Check base permission
        required_perm = Permission("triage", "read")
        if not self.check_permission(security_context, required_perm):
            raise AuthorizationError(
                message="Insufficient permissions for triage access",
                details={
                    "error_code": "PERMISSION_DENIED",
                    "required": f"{required_perm.resource}:{required_perm.action}",
                    "user_role": role
                },
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Student access control: students can only access their own triage
        if role == "student" and student_id_in_path:
            if user_student_id != student_id_in_path:
                raise AuthorizationError(
                    message="Student can only access their own triage data",
                    details={
                        "error_code": "SCOPE_VIOLATION",
                        "user_student_id": user_student_id,
                        "requested_student_id": student_id_in_path,
                        "role": role
                    },
                    status_code=status.HTTP_403_FORBIDDEN
                )

        return {
            "access_granted": True,
            "role": role,
            "student_id": user_student_id,
            "scope_check": role != "student" or student_id_in_path is None or user_student_id == student_id_in_path
        }

    def check_dapr_invocation_permission(self, security_context: Dict, target_agent: str) -> Dict:
        """
        Verify permission to invoke specific Dapr agent

        Args:
            security_context: User context
            target_agent: Target agent name

        Returns:
            Dict with permission decision
        """
        role = security_context.get("role")
        user_student_id = security_context.get("student_id")

        # Permission map by agent
        agent_permissions = {
            "debug-agent": ["student", "instructor", "admin"],
            "concepts-agent": ["student", "instructor", "admin"],
            "exercise-agent": ["student", "instructor", "admin"],
            "progress-agent": ["student", "instructor", "admin"],
            "review-agent": ["instructor", "admin"]  # More privileged
        }

        allowed_roles = agent_permissions.get(target_agent, [])

        if role not in allowed_roles:
            raise AuthorizationError(
                message=f"Role '{role}' cannot invoke agent '{target_agent}'",
                details={
                    "error_code": "AGENT_ACCESS_DENIED",
                    "target_agent": target_agent,
                    "allowed_roles": allowed_roles,
                    "user_role": role
                },
                status_code=status.HTTP_403_FORBIDDEN
            )

        return {
            "allowed": True,
            "target_agent": target_agent,
            "role": role,
            "student_id": user_student_id
        }

    def get_user_permissions(self, security_context: Dict) -> List[Permission]:
        """Get all permissions for user's role"""
        role = security_context.get("role")
        return self.role_permissions.get(role, [])

    def has_admin_access(self, security_context: Dict) -> bool:
        """Check if user has admin access"""
        return security_context.get("role") == "admin"


# Global authorization middleware instance
authz_middleware = AuthorizationMiddleware()


async def authorization_middleware(request: Request, call_next):
    """
    FastAPI middleware for authorization

    This middleware assumes security_context_middleware has already
    run and attached security_context to request.state
    """
    # Get security context from auth middleware
    security_context = getattr(request.state, "security_context", None)

    if not security_context:
        # This should not happen if auth middleware is configured correctly
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security context missing"
        )

    # Extract student_id from path if present
    path_params = request.path_params
    student_id_in_path = path_params.get("student_id") if path_params else None

    # Verify triage access
    try:
        access_decision = authz_middleware.verify_triage_access(
            security_context, student_id_in_path
        )

        # Store authorization result in request state
        request.state.authorization = access_decision

        # Continue to endpoint
        response = await call_next(request)

        # Add authorization headers to response
        response.headers["X-User-Role"] = security_context["role"]
        response.headers["X-Access-Granted"] = "true"

        return response

    except AuthorizationError as e:
        # Log authorization failure (audit trail)
        print(f"AUTHZ_FAILURE: {security_context['student_id']} - {e.message}")

        return HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )


# Convenience functions for dependency injection
def get_current_user(request: Request) -> Dict:
    """Get current user's security context"""
    return getattr(request.state, "security_context", None)


def require_permission(permission: Permission):
    """
    Dependency for FastAPI route handlers

    Usage:
        @app.post("/triage")
        async def triage_endpoint(
            current_user: Dict = Depends(require_permission(Permission("triage", "read")))
        ):
            # Only executed if permission granted
    """
    def permission_checker(request: Request) -> Dict:
        security_context = getattr(request.state, "security_context", None)
        if not security_context:
            raise HTTPException(status_code=500, detail="Security context error")

        if not authz_middleware.check_permission(security_context, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "PERMISSION_DENIED",
                    "required": f"{permission.resource}:{permission.action}",
                    "user_role": security_context.get("role")
                }
            )

        return security_context

    return permission_checker


if __name__ == "__main__":
    # Test authorization logic
    print("=== Authorization Middleware Test ===")

    test_contexts = [
        {"student_id": "student-123", "role": "student"},
        {"student_id": "student-456", "role": "instructor"},
        {"student_id": "student-789", "role": "admin"}
    ]

    middleware = AuthorizationMiddleware()

    # Test triage access
    for context in test_contexts:
        try:
            result = middleware.verify_triage_access(context)
            print(f"✅ {context['role']}: {result}")
        except AuthorizationError as e:
            print(f"❌ {context['role']}: {e.message}")

    # Test agent invocation
    print("\n--- Agent Invocation Tests ---")
    for context in test_contexts:
        for agent in ["debug-agent", "review-agent"]:
            try:
                result = middleware.check_dapr_invocation_permission(context, agent)
                print(f"✅ {context['role']} → {agent}: Allowed")
            except AuthorizationError:
                print(f"❌ {context['role']} → {agent}: Denied")

    # Test specific permissions
    print("\n--- Specific Permission Tests ---")
    test_perm = Permission("triage", "read")
    for context in test_contexts:
        allowed = middleware.check_permission(context, test_perm)
        print(f"{'✅' if allowed else '❌'} {context['role']}: triage:read -> {allowed}")