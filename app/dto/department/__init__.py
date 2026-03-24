"""
Department 模块 DTO
"""
from app.dto.department.department_request import (
    DepartmentRequest,
    SetDepartmentUsersRequest,
    AddDepartmentUserRequest,
    RemoveDepartmentUserRequest,
)
from app.dto.department.department_response import (
    DepartmentResponse,
    DepartmentTreeResponse,
    DepartmentUserResponse,
)

__all__ = [
    "DepartmentRequest",
    "SetDepartmentUsersRequest",
    "AddDepartmentUserRequest",
    "RemoveDepartmentUserRequest",
    "DepartmentResponse",
    "DepartmentTreeResponse",
    "DepartmentUserResponse",
]