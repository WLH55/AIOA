"""
部门查询工具

提供获取部门树和部门详情的能力
"""
import logging
from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.repository.department_repository import DepartmentRepository

logger = logging.getLogger(__name__)


class DepartmentIdInput(BaseModel):
    """部门 ID 输入"""
    departmentId: str = Field(default="", description="部门ID，为空时返回所有部门")


async def _get_department_tree() -> str:
    """
    获取部门树结构

    Returns:
        格式化的部门树文本
    """
    departments = await DepartmentRepository.find_all()
    if not departments:
        return "暂无部门数据"
    # 构建树形结构
    dept_map = {}
    root_depts = []
    for dept in departments:
        dept_id = str(dept.id)
        dept_map[dept_id] = {
            "id": dept_id,
            "name": dept.name,
            "parentId": dept.parentId,
            "level": dept.level,
            "children": [],
        }
    for dept_id, dept_info in dept_map.items():
        parent_id = dept_info["parentId"]
        if not parent_id or parent_id not in dept_map:
            root_depts.append(dept_info)
        else:
            dept_map[parent_id]["children"].append(dept_info)
    # 递归格式化输出
    lines = []
    for root in root_depts:
        _format_dept_node(root, lines, 0)
    return "部门结构：\n" + "\n".join(lines) if lines else "暂无部门数据"


def _format_dept_node(node: dict, lines: List[str], depth: int) -> None:
    """
    递归格式化部门节点

    Args:
        node: 部门节点数据
        lines: 输出行列表
        depth: 缩进层级
    """
    indent = "  " * depth + "- " if depth > 0 else "- "
    lines.append(f"{indent}{node['name']} (ID: {node['id']})")
    for child in node.get("children", []):
        _format_dept_node(child, lines, depth + 1)


async def _get_department_info(departmentId: str) -> str:
    """
    获取部门详情

    Args:
        departmentId: 部门 ID

    Returns:
        格式化的部门详情文本
    """
    if not departmentId:
        return await _get_department_tree()
    dept = await DepartmentRepository.find_by_id(departmentId)
    if not dept:
        return f"未找到部门：{departmentId}"
    return (
        f"部门详情：\n"
        f"- 部门名称：{dept.name}\n"
        f"- 部门ID：{str(dept.id)}\n"
        f"- 层级：{dept.level}\n"
        f"- 父部门ID：{dept.parentId or '无（顶级部门）'}"
    )


def get_department_tools() -> List[StructuredTool]:
    """获取部门查询工具列表"""
    return [
        StructuredTool.from_function(
            coroutine=_get_department_tree,
            name="getDepartmentTree",
            description="获取完整的部门树结构。当用户询问部门架构、组织结构、有哪些部门时调用此工具。",
        ),
        StructuredTool.from_function(
            coroutine=_get_department_info,
            name="getDepartmentInfo",
            description="获取指定部门的详细信息。当用户询问某个具体部门的情况时调用。",
            args_schema=DepartmentIdInput,
        ),
    ]
