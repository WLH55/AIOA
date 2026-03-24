"""
部门服务层

处理部门相关的业务逻辑
"""
import logging
import time
from typing import List, Dict, Set, Optional

from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.models.department import Department
from app.models.department_user import DepartmentUser
from app.models.user import User
from app.repository.department_repository import DepartmentRepository
from app.repository.department_user_repository import DepartmentUserRepository
from app.repository.user_repository import UserRepository
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

logger = logging.getLogger(__name__)


class DepartmentService:
    """
    部门服务类

    提供部门 CRUD、树形结构、用户关联等业务逻辑
    """

    @staticmethod
    async def soa() -> DepartmentTreeResponse:
        """
        获取部门树结构

        Returns:
            部门树响应 DTO
        """
        # 获取所有部门
        all_departments = await DepartmentRepository.find_all()

        # 收集所有负责人ID
        leader_ids: Set[str] = {
            d.leaderId for d in all_departments
            if d.leaderId
        }

        # 批量查询所有负责人信息
        leader_map: Dict[str, str] = {}
        if leader_ids:
            leaders = await UserRepository.find_by_ids(list(leader_ids))
            leader_map = {str(l.id): l.name for l in leaders}

        # 查询所有部门用户关联
        all_dep_users = await DepartmentUserRepository.find_all()

        # 收集所有用户ID
        all_user_ids: Set[str] = {du.userId for du in all_dep_users}

        # 批量查询所有用户信息
        user_map: Dict[str, str] = {}
        if all_user_ids:
            users = await UserRepository.find_by_ids(list(all_user_ids))
            user_map = {str(u.id): u.name for u in users}

        # 统计每个部门的用户数量和用户列表
        dep_user_count_map: Dict[str, int] = {}
        dep_users_map: Dict[str, List[DepartmentUserResponse]] = {}

        for dep_user in all_dep_users:
            dep_user_count_map[dep_user.depId] = dep_user_count_map.get(dep_user.depId, 0) + 1

            user_name = user_map.get(dep_user.userId, "")
            user_resp = DepartmentUserResponse(
                id=str(dep_user.id),
                user_id=dep_user.userId,
                dep_id=dep_user.depId,
                user_name=user_name,
            )
            if dep_user.depId not in dep_users_map:
                dep_users_map[dep_user.depId] = []
            dep_users_map[dep_user.depId].append(user_resp)

        # 按父路径分组部门
        group_dep: Dict[str, List[DepartmentResponse]] = {}
        root_dep: List[DepartmentResponse] = []

        for dep in all_departments:
            dep_resp = DepartmentService._build_department_response(dep)

            # 填充负责人名称
            if dep.leaderId and dep.leaderId in leader_map:
                dep_resp.leader = leader_map[dep.leaderId]

            # 填充部门成员数量
            dep_resp.count = dep_user_count_map.get(str(dep.id), 0)

            # 填充部门用户列表
            dep_resp.users = dep_users_map.get(str(dep.id), [])

            if not dep.parentPath:
                # 根部门
                root_dep.append(dep_resp)
            else:
                # 子部门
                if dep.parentPath not in group_dep:
                    group_dep[dep.parentPath] = []
                group_dep[dep.parentPath].append(dep_resp)

        # 构建部门树
        DepartmentService._build_tree(root_dep, group_dep)

        return DepartmentTreeResponse(child=root_dep)

    @staticmethod
    async def info(department_id: str) -> DepartmentResponse:
        """
        获取部门详情

        Args:
            department_id: 部门ID

        Returns:
            部门详情响应 DTO

        Raises:
            ResourceNotFoundException: 部门不存在
        """
        department = await DepartmentRepository.find_by_id(department_id)
        if not department:
            raise ResourceNotFoundException("部门不存在")

        response = DepartmentService._build_department_response(department)

        # 获取负责人名称
        if department.leaderId:
            leader = await UserRepository.find_by_id(department.leaderId)
            if leader:
                response.leader = leader.name

        return response

    @staticmethod
    async def create(request: DepartmentRequest) -> None:
        """
        创建部门

        Args:
            request: 部门请求 DTO

        Raises:
            BusinessValidationException: 部门名称已存在或父部门不存在
        """
        # 检查部门名称是否已存在
        existing_dep = await DepartmentRepository.find_by_name(request.name)
        if existing_dep:
            raise BusinessValidationException("已存在该部门")

        # 构建父路径
        parent_path = ""
        if request.parent_id:
            parent_dep = await DepartmentRepository.find_by_id(request.parent_id)
            if not parent_dep:
                raise ResourceNotFoundException("父部门不存在")
            parent_path = DepartmentService._build_parent_path(parent_dep.parentPath, request.parent_id)

        # 创建部门
        department = Department(
            name=request.name,
            parentId=request.parent_id,
            parentPath=parent_path,
            level=request.level or 1,
            leaderId=request.leader_id,
            userCount=1,
        )

        saved = await DepartmentRepository.create(department)
        logger.info(f"创建部门成功: id={saved.id}")

        # 将负责人添加到部门
        await DepartmentService.add_department_user(
            AddDepartmentUserRequest(dep_id=str(saved.id), user_id=request.leader_id)
        )

    @staticmethod
    async def edit(request: DepartmentRequest) -> None:
        """
        编辑部门

        Args:
            request: 部门请求 DTO

        Raises:
            BusinessValidationException: 部门ID不能为空或部门名称已存在
            ResourceNotFoundException: 部门不存在
        """
        if not request.id:
            raise BusinessValidationException("部门ID不能为空")

        department = await DepartmentRepository.find_by_id(request.id)
        if not department:
            raise ResourceNotFoundException("部门不存在")

        # 检查新名称是否重复
        existing_dep = await DepartmentRepository.find_by_name(request.name)
        if existing_dep and str(existing_dep.id) != request.id:
            raise BusinessValidationException("已存在该部门")

        department.name = request.name
        department.parentId = request.parent_id
        department.level = request.level or department.level
        department.leaderId = request.leader_id

        await DepartmentRepository.update(department)
        logger.info(f"编辑部门成功: id={request.id}")

    @staticmethod
    async def delete(department_id: str) -> None:
        """
        删除部门

        Args:
            department_id: 部门ID
        """
        department = await DepartmentRepository.find_by_id(department_id)

        if not department:
            return

        # 查找部门下的用户
        dep_users = await DepartmentUserRepository.find_by_dep_id(department_id)

        if not dep_users:
            await DepartmentRepository.delete(department_id)
            logger.info(f"删除部门成功: id={department_id}")
            return

        # 检查是否只有负责人
        if len(dep_users) > 1 or dep_users[0].userId != department.leaderId:
            raise BusinessValidationException("该部门下还存在用户，不能删除该部门")

        # 只有负责人的情况下，先删除负责人关联
        leader_id = department.leaderId

        for du in dep_users:
            if du.userId == leader_id:
                await DepartmentUserRepository.delete(str(du.id))
                break

        # 从父部门删除负责人
        if department.parentPath:
            parent_ids = DepartmentService._parse_parent_path(department.parentPath)
            leader_dep_ids: Set[str] = set()

            # 获取负责人当前所在的所有部门ID
            all_user_deps = await DepartmentUserRepository.find_all()
            for ud in all_user_deps:
                if ud.userId == leader_id and ud.depId != department_id:
                    leader_dep_ids.add(ud.depId)

            # 如果负责人已经不在任何部门了，从所有父部门删除
            if not leader_dep_ids:
                for parent_id in parent_ids:
                    parent_dep_users = await DepartmentUserRepository.find_by_dep_id(parent_id)
                    for pdu in parent_dep_users:
                        if pdu.userId == leader_id:
                            await DepartmentUserRepository.delete(str(pdu.id))
                            break

        # 删除部门本身
        await DepartmentRepository.delete(department_id)
        logger.info(f"删除部门成功: id={department_id}")

    @staticmethod
    async def set_department_users(request: SetDepartmentUsersRequest) -> None:
        """
        设置部门用户

        Args:
            request: 设置部门用户请求 DTO
        """
        department = await DepartmentRepository.find_by_id(request.dep_id)
        if not department:
            raise ResourceNotFoundException("部门不存在")

        # 获取当前部门的所有用户
        current_dep_users = await DepartmentUserRepository.find_by_dep_id(request.dep_id)

        current_user_set = {du.userId for du in current_dep_users}
        new_user_set = set(request.user_ids or [])

        # 删除不在新列表中的用户
        for du in current_dep_users:
            if du.userId not in new_user_set and du.userId != department.leaderId:
                try:
                    await DepartmentService.remove_department_user(
                        RemoveDepartmentUserRequest(dep_id=request.dep_id, user_id=du.userId)
                    )
                except Exception as e:
                    logger.warning(f"删除部门用户失败: {e}")

        # 添加新用户
        for user_id in new_user_set:
            if user_id not in current_user_set:
                try:
                    await DepartmentService.add_department_user(
                        AddDepartmentUserRequest(dep_id=request.dep_id, user_id=user_id)
                    )
                except Exception as e:
                    logger.warning(f"添加部门用户失败: {e}")

        logger.info(f"设置部门用户成功: depId={request.dep_id}")

    @staticmethod
    async def add_department_user(request: AddDepartmentUserRequest) -> None:
        """
        添加部门员工（级联到上级部门）

        Args:
            request: 添加部门员工请求 DTO

        Raises:
            ResourceNotFoundException: 部门或用户不存在
            BusinessValidationException: 用户已在该部门中
        """
        # 验证部门是否存在
        department = await DepartmentRepository.find_by_id(request.dep_id)
        if not department:
            raise ResourceNotFoundException("部门不存在")

        # 验证用户是否存在
        user = await UserRepository.find_by_id(request.user_id)
        if not user:
            raise ResourceNotFoundException("用户不存在")

        # 检查用户是否已在该部门
        if await DepartmentUserRepository.exists_by_dep_and_user(request.dep_id, request.user_id):
            raise BusinessValidationException("该用户已在此部门中")

        # 添加用户到当前部门
        dep_user = DepartmentUser(depId=request.dep_id, userId=request.user_id)
        await DepartmentUserRepository.create(dep_user)

        # 如果有上级部门，将用户也添加到所有上级部门
        if department.parentPath:
            parent_ids = DepartmentService._parse_parent_path(department.parentPath)

            for parent_id in parent_ids:
                if not await DepartmentUserRepository.exists_by_dep_and_user(parent_id, request.user_id):
                    parent_dep_user = DepartmentUser(depId=parent_id, userId=request.user_id)
                    await DepartmentUserRepository.create(parent_dep_user)

        logger.info(f"添加部门用户成功: depId={request.dep_id}, userId={request.user_id}")

    @staticmethod
    async def remove_department_user(request: RemoveDepartmentUserRequest) -> None:
        """
        删除部门员工（级联从上级部门删除）

        Args:
            request: 删除部门员工请求 DTO

        Raises:
            ResourceNotFoundException: 部门不存在
            BusinessValidationException: 不能删除部门负责人或用户不在此部门中
        """
        # 验证部门是否存在
        department = await DepartmentRepository.find_by_id(request.dep_id)
        if not department:
            raise ResourceNotFoundException("部门不存在")

        # 不能删除部门负责人
        if request.user_id == department.leaderId:
            raise BusinessValidationException("不能删除部门负责人")

        # 查找用户在该部门的关联记录
        dep_users = await DepartmentUserRepository.find_by_dep_id(request.dep_id)
        target_du = None
        for du in dep_users:
            if du.userId == request.user_id:
                target_du = du
                break

        if not target_du:
            raise BusinessValidationException("该用户不在此部门中")

        # 删除用户与当前部门的关联
        await DepartmentUserRepository.delete(str(target_du.id))

        # 如果有上级部门，智能地从上级部门删除该用户
        if department.parentPath:
            parent_ids = DepartmentService._parse_parent_path(department.parentPath)

            # 获取该用户当前所在的所有部门ID
            all_user_deps = await DepartmentUserRepository.find_all()
            user_dep_ids: Set[str] = set()
            for ud in all_user_deps:
                if ud.userId == request.user_id and ud.depId != request.dep_id:
                    user_dep_ids.add(ud.depId)

            # 如果用户已经不在任何部门了，从所有父部门删除
            if not user_dep_ids:
                for parent_id in parent_ids:
                    parent_dep_users = await DepartmentUserRepository.find_by_dep_id(parent_id)
                    for pdu in parent_dep_users:
                        if pdu.userId == request.user_id:
                            await DepartmentUserRepository.delete(str(pdu.id))
                            break
            else:
                # 获取所有部门信息
                all_deps = await DepartmentRepository.find_all()
                dep_map = {str(d.id): d for d in all_deps}

                # 反转顺序，从近到远处理
                parent_ids = list(reversed(parent_ids))

                for parent_id in parent_ids:
                    still_under_this_parent = False

                    for user_dep_id in user_dep_ids:
                        if user_dep_id == parent_id:
                            continue

                        user_dep = dep_map.get(user_dep_id)
                        if not user_dep:
                            continue

                        if user_dep.parentPath and parent_id in user_dep.parentPath:
                            still_under_this_parent = True
                            break
                        if parent_id == user_dep.parentId:
                            still_under_this_parent = True
                            break

                    if not still_under_this_parent:
                        parent_dep_users = await DepartmentUserRepository.find_by_dep_id(parent_id)
                        for pdu in parent_dep_users:
                            if pdu.userId == request.user_id:
                                await DepartmentUserRepository.delete(str(pdu.id))
                                user_dep_ids.discard(parent_id)
                                break

        logger.info(f"删除部门用户成功: depId={request.dep_id}, userId={request.user_id}")

    @staticmethod
    async def department_user_info(user_id: str) -> DepartmentResponse:
        """
        获取用户部门信息（包含完整的上级部门层级）

        Args:
            user_id: 用户ID

        Returns:
            部门响应 DTO

        Raises:
            ResourceNotFoundException: 用户未关联任何部门
        """
        # 根据用户ID查找用户所属的部门关联
        dep_users = await DepartmentUserRepository.find_by_user_id(user_id)
        if not dep_users:
            raise ResourceNotFoundException("用户未关联任何部门")

        dep_user = dep_users[0]

        # 根据部门ID查找部门信息
        department = await DepartmentRepository.find_by_id(dep_user.depId)
        if not department:
            raise ResourceNotFoundException("用户关联的部门不存在")

        # 如果是根部门，直接返回
        if not department.parentPath:
            return DepartmentService._build_department_response(department)

        # 解析父路径，获取所有上级部门ID
        parent_ids = DepartmentService._parse_parent_path(department.parentPath)
        parent_deps = await DepartmentRepository.find_by_ids(parent_ids)
        dep_map = {str(d.id): d for d in parent_deps}

        # 构建完整的部门层级结构
        root = None
        node = None

        for pid in parent_ids:
            dep = dep_map.get(pid)
            if not dep:
                continue

            if root is None:
                root = DepartmentService._build_department_response(dep)
                node = root
                continue

            tmp = DepartmentService._build_department_response(dep)
            if node:
                if not node.child:
                    node.child = []
                node.child.append(tmp)
            node = tmp

        # 将用户直接关联的部门添加为最后一级
        if node:
            if not node.child:
                node.child = []
            node.child.append(DepartmentService._build_department_response(department))

        return root if root else DepartmentService._build_department_response(department)

    @staticmethod
    def _build_tree(
        root_dep: List[DepartmentResponse],
        group_dep: Dict[str, List[DepartmentResponse]]
    ) -> None:
        """
        递归构建部门树结构
        """
        for dep in root_dep:
            path = DepartmentService._build_parent_path(dep.parent_path, dep.id)

            children = group_dep.get(path)
            if children:
                DepartmentService._build_tree(children, group_dep)
                dep.child = children

    @staticmethod
    def _build_parent_path(parent_path: Optional[str], id: str) -> str:
        """
        构建父路径
        """
        if not parent_path:
            return f":{id}"
        return f"{parent_path}:{id}"

    @staticmethod
    def _parse_parent_path(parent_path: Optional[str]) -> List[str]:
        """
        解析父路径
        """
        if not parent_path:
            return []
        return [p for p in parent_path.split(":") if p]

    @staticmethod
    def _build_department_response(department: Department) -> DepartmentResponse:
        """
        构建部门响应对象
        """
        return DepartmentResponse(
            id=str(department.id),
            name=department.name,
            parent_id=department.parentId,
            parent_path=department.parentPath,
            level=department.level,
            leader_id=department.leaderId,
            count=department.userCount,
        )