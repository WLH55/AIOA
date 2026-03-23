"""
数据模型模块
"""
from app.models.user import User
from app.models.todo import Todo, UserTodo, TodoRecord
from app.models.approval import Approval, Approver, MakeCard, Leave, GoOut
from app.models.chat_log import ChatLog
from app.models.department import Department
from app.models.department_user import DepartmentUser

__all__ = [
    # 主文档
    "User",
    "Todo",
    "Approval",
    "ChatLog",
    "Department",
    "DepartmentUser",
    # 内嵌文档
    "UserTodo",
    "TodoRecord",
    "Approver",
    "MakeCard",
    "Leave",
    "GoOut",
]