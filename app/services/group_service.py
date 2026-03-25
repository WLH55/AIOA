"""
群组服务层

处理群组相关的业务逻辑
"""
import logging
import json
from typing import List

from app.config.exceptions import ResourceNotFoundException, BusinessValidationException
from app.models.group import Group
from app.models.user import User
from app.models.chat_log import ChatLog
from app.repository.group_repository import GroupRepository
from app.repository.user_repository import UserRepository
from app.services.ws_manager import ws_manager
from app.dto.group.group_request import (
    CreateGroupRequest,
    GroupListRequest,
    InviteMemberRequest,
    RemoveMemberRequest,
    UpdateGroupRequest,
)
from app.dto.group.group_response import (
    GroupResponse,
    GroupListResponse,
    GroupListItemResponse,
    GroupMemberResponse,
)

logger = logging.getLogger(__name__)

# 常量定义
MAX_MEMBERS = 100  # 群组成员上限
STATUS_NORMAL = 1  # 正常状态
STATUS_DISMISSED = 2  # 已解散状态


class GroupService:
    """
    群组服务类

    提供群组 CRUD、成员管理等业务逻辑
    """

    @staticmethod
    async def create(request: CreateGroupRequest, current_user: User) -> str:
        """
        创建群组

        Args:
            request: 创建群组请求 DTO
            current_user: 当前用户

        Returns:
            创建的群组ID

        Raises:
            BusinessValidationException: 成员数量超限
        """
        logger.info(f"创建群组: name={request.name}")

        current_user_id = str(current_user.id)

        # 验证成员数量
        unique_members = set(request.memberIds)
        if len(unique_members) > MAX_MEMBERS:
            raise BusinessValidationException(f"群组成员数量不能超过{MAX_MEMBERS}人")

        # 确保创建者在成员列表中
        if current_user_id not in unique_members:
            unique_members.add(current_user_id)

        # 创建群组
        group = Group(
            name=request.name,
            avatar=request.avatar,
            ownerId=current_user_id,
            memberIds=list(unique_members),
            status=STATUS_NORMAL,
        )

        saved = await GroupRepository.create(group)
        logger.info(f"创建群组成功: id={saved.id}")

        # 发送系统消息通知
        await GroupService._send_system_message(
            group_id=str(saved.id),
            system_type="group_create",
            content=f"{current_user.name} 创建了群组",
            group_info={
                "groupId": str(saved.id),
                "groupName": saved.name,
                "memberIds": saved.memberIds,
                "creatorId": current_user_id,
            },
        )

        return str(saved.id)

    @staticmethod
    async def list(request: GroupListRequest, current_user: User) -> GroupListResponse:
        """
        获取群组列表

        Args:
            request: 群组列表请求 DTO
            current_user: 当前用户

        Returns:
            群组列表响应 DTO
        """
        logger.info(f"获取群组列表: page={request.page}, count={request.count}")

        current_user_id = str(current_user.id)

        groups, total = await GroupRepository.find_by_member_id(
            member_id=current_user_id,
            status=STATUS_NORMAL,
            page=request.page,
            page_size=request.count,
        )

        # 收集群主ID
        owner_ids = [group.ownerId for group in groups]

        # 批量查询群主信息
        owners = await UserRepository.find_by_ids(owner_ids)
        owner_map = {str(owner.id): owner for owner in owners}

        # 构建响应列表
        data: List[GroupListItemResponse] = []
        for group in groups:
            owner = owner_map.get(group.ownerId)
            data.append(GroupListItemResponse(
                id=str(group.id),
                name=group.name,
                avatar=group.avatar,
                ownerId=group.ownerId,
                ownerName=owner.name if owner else "",
                memberCount=len(group.memberIds),
                status=group.status,
                createAt=group.createAt,
            ))

        return GroupListResponse(count=total, data=data)

    @staticmethod
    async def info(group_id: str, current_user: User) -> GroupResponse:
        """
        获取群组详情

        Args:
            group_id: 群组ID
            current_user: 当前用户

        Returns:
            群组详情响应 DTO

        Raises:
            ResourceNotFoundException: 群组不存在
            BusinessValidationException: 不是群组成员
        """
        group = await GroupRepository.find_by_id(group_id)
        if not group:
            raise ResourceNotFoundException("群组不存在")

        current_user_id = str(current_user.id)

        # 验证是否为群组成员
        if current_user_id not in group.memberIds:
            raise BusinessValidationException("不是群组成员")

        # 查询群主信息
        owner = await UserRepository.find_by_id(group.ownerId)

        # 查询所有成员信息
        members = await UserRepository.find_by_ids(group.memberIds)
        member_map = {str(member.id): member for member in members}

        # 构建成员详情列表
        member_details: List[GroupMemberResponse] = []
        for member_id in group.memberIds:
            member = member_map.get(member_id)
            if member:
                member_details.append(GroupMemberResponse(
                    userId=member_id,
                    userName=member.name,
                    isOwner=(member_id == group.ownerId),
                ))

        return GroupResponse(
            id=str(group.id),
            name=group.name,
            avatar=group.avatar,
            ownerId=group.ownerId,
            ownerName=owner.name if owner else "",
            memberIds=group.memberIds,
            members=member_details,
            memberCount=len(group.memberIds),
            status=group.status,
            createAt=group.createAt,
            updateAt=group.updateAt,
        )

    @staticmethod
    async def invite(group_id: str, request: InviteMemberRequest, current_user: User) -> None:
        """
        邀请成员

        Args:
            group_id: 群组ID
            request: 邀请成员请求 DTO
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 群组不存在
            BusinessValidationException: 无权限、成员已存在、成员超限
        """
        logger.info(f"邀请成员: group_id={group_id}, memberIds={request.memberIds}")

        group = await GroupRepository.find_by_id(group_id)
        if not group:
            raise ResourceNotFoundException("群组不存在")

        current_user_id = str(current_user.id)

        # 验证权限
        if group.ownerId != current_user_id:
            raise BusinessValidationException("只有群主可以邀请成员")

        # 验证群组状态
        if group.status != STATUS_NORMAL:
            raise BusinessValidationException("群组已解散")

        # 检查成员是否已存在
        existing_members = set(group.memberIds)
        new_members = set(request.memberIds)
        duplicates = existing_members & new_members
        if duplicates:
            raise BusinessValidationException(f"用户已在群组中: {list(duplicates)}")

        # 验证成员数量
        if len(existing_members) + len(new_members) > MAX_MEMBERS:
            raise BusinessValidationException(f"群组成员数量不能超过{MAX_MEMBERS}人")

        # 添加新成员
        group.memberIds.extend(list(new_members))
        group.update_timestamp()
        await GroupRepository.update(group)

        # 查询新成员信息
        new_member_users = await UserRepository.find_by_ids(list(new_members))
        new_member_names = [user.name for user in new_member_users]

        # 发送系统消息通知
        for name in new_member_names:
            await GroupService._send_system_message(
                group_id=group_id,
                system_type="group_invite",
                content=f"{current_user.name} 邀请了 {name} 加入群组",
            )

        logger.info(f"邀请成员成功: group_id={group_id}, new_members={list(new_members)}")

    @staticmethod
    async def remove(group_id: str, request: RemoveMemberRequest, current_user: User) -> None:
        """
        移除成员

        Args:
            group_id: 群组ID
            request: 移除成员请求 DTO
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 群组不存在
            BusinessValidationException: 无权限、不能移除自己
        """
        logger.info(f"移除成员: group_id={group_id}, memberId={request.memberId}")

        group = await GroupRepository.find_by_id(group_id)
        if not group:
            raise ResourceNotFoundException("群组不存在")

        current_user_id = str(current_user.id)

        # 验证权限
        if group.ownerId != current_user_id:
            raise BusinessValidationException("只有群主可以移除成员")

        # 验证群组状态
        if group.status != STATUS_NORMAL:
            raise BusinessValidationException("群组已解散")

        # 验证不能移除自己
        if request.memberId == current_user_id:
            raise BusinessValidationException("不能移除自己，请使用退出群组功能")

        # 验证成员是否存在
        if request.memberId not in group.memberIds:
            raise BusinessValidationException("用户不在群组中")

        # 移除成员
        group.memberIds.remove(request.memberId)
        group.update_timestamp()
        await GroupRepository.update(group)

        # 查询被移除成员信息
        removed_user = await UserRepository.find_by_id(request.memberId)

        # 发送系统消息通知
        await GroupService._send_system_message(
            group_id=group_id,
            system_type="group_remove",
            content=f"{removed_user.name if removed_user else request.memberId} 被移出群组",
        )

        logger.info(f"移除成员成功: group_id={group_id}, memberId={request.memberId}")

    @staticmethod
    async def exit(group_id: str, current_user: User) -> None:
        """
        退出群组

        Args:
            group_id: 群组ID
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 群组不存在
            BusinessValidationException: 群主不能退出
        """
        logger.info(f"退出群组: group_id={group_id}")

        group = await GroupRepository.find_by_id(group_id)
        if not group:
            raise ResourceNotFoundException("群组不存在")

        current_user_id = str(current_user.id)

        # 验证群主不能退出
        if group.ownerId == current_user_id:
            raise BusinessValidationException("群主不能退出群组")

        # 验证群组状态
        if group.status != STATUS_NORMAL:
            raise BusinessValidationException("群组已解散")

        # 验证是否为成员
        if current_user_id not in group.memberIds:
            raise BusinessValidationException("不是群组成员")

        # 退出群组
        group.memberIds.remove(current_user_id)
        group.update_timestamp()
        await GroupRepository.update(group)

        # 发送系统消息通知
        await GroupService._send_system_message(
            group_id=group_id,
            system_type="group_exit",
            content=f"{current_user.name} 退出了群组",
        )

        logger.info(f"退出群组成功: group_id={group_id}, userId={current_user_id}")

    @staticmethod
    async def update(group_id: str, request: UpdateGroupRequest, current_user: User) -> None:
        """
        修改群组信息

        Args:
            group_id: 群组ID
            request: 修改群组信息请求 DTO
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 群组不存在
            BusinessValidationException: 无权限
        """
        logger.info(f"修改群组信息: group_id={group_id}")

        group = await GroupRepository.find_by_id(group_id)
        if not group:
            raise ResourceNotFoundException("群组不存在")

        current_user_id = str(current_user.id)

        # 验证权限
        if group.ownerId != current_user_id:
            raise BusinessValidationException("只有群主可以修改群组信息")

        # 验证群组状态
        if group.status != STATUS_NORMAL:
            raise BusinessValidationException("群组已解散")

        # 更新信息
        if request.name is not None:
            group.name = request.name
        if request.avatar is not None:
            group.avatar = request.avatar

        group.update_timestamp()
        await GroupRepository.update(group)

        logger.info(f"修改群组信息成功: group_id={group_id}")

    @staticmethod
    async def dismiss(group_id: str, current_user: User) -> None:
        """
        解散群组

        Args:
            group_id: 群组ID
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 群组不存在
            BusinessValidationException: 无权限
        """
        logger.info(f"解散群组: group_id={group_id}")

        group = await GroupRepository.find_by_id(group_id)
        if not group:
            raise ResourceNotFoundException("群组不存在")

        current_user_id = str(current_user.id)

        # 验证权限
        if group.ownerId != current_user_id:
            raise BusinessValidationException("只有群主可以解散群组")

        # 验证群组状态
        if group.status != STATUS_NORMAL:
            raise BusinessValidationException("群组已解散")

        # 更新状态为已解散
        group.status = STATUS_DISMISSED
        group.update_timestamp()
        await GroupRepository.update(group)

        # 发送系统消息通知
        await GroupService._send_system_message(
            group_id=group_id,
            system_type="group_dismiss",
            content="群组已解散",
        )

        logger.info(f"解散群组成功: group_id={group_id}")

    @staticmethod
    async def _send_system_message(
        group_id: str,
        system_type: str,
        content: str,
        group_info: dict = None,
    ) -> None:
        """
        发送群组系统消息

        Args:
            group_id: 群组ID
            system_type: 系统消息类型
            content: 消息内容
            group_info: 群组信息（可选）
        """
        try:
            # 构建系统消息
            message = {
                "type": "message",
                "systemType": system_type,
                "conversationId": group_id,
                "chatType": 1,  # 群聊
                "content": content,
            }

            if group_info:
                message["groupInfo"] = group_info

            # 通过 WebSocket 广播消息
            await ws_manager.broadcast(json.dumps(message), group_id)

            # 保存系统消息到 ChatLog
            chat_log = ChatLog(
                conversationId=group_id,
                sendId="system",
                recvId=None,
                chatType=1,
                msgContent=content,
            )
            await chat_log.insert()

        except Exception as e:
            logger.error(f"发送系统消息失败: {e}")
