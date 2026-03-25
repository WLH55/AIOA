# 群组功能实施计划

## 1. 文件清单

### 1.1 新增文件

| 路径 | 说明 |
|------|------|
| `app/models/group.py` | Group 数据模型 |
| `app/dto/group/group_request.py` | 群组请求 DTO |
| `app/dto/group/group_response.py` | 群组响应 DTO |
| `app/repository/group_repository.py` | 群组数据访问层 |
| `app/services/group_service.py` | 群组业务逻辑层 |
| `app/routers/group.py` | 群组路由 |

### 1.2 修改文件

| 路径 | 说明 |
|------|------|
| `app/main.py` | 注册群组路由 |
| `app/models/__init__.py` | 导出 Group 模型 |
| `app/dto/ws/message.py` | 更新 GroupInfo 定义（如需） |

---

## 2. 实施步骤

### 步骤 1: 创建 Group 数据模型

**文件**: `app/models/group.py`

```python
"""
群组实体模型
使用 Beanie ODM 定义 MongoDB Document
"""
import time
from typing import Optional, List
from pydantic import Field
from beanie import Document, Indexed


class Group(Document):
    """群组文档模型"""

    # 基本信息
    name: Indexed(str) = Field(..., min_length=1, max_length=50, description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    ownerId: str = Field(..., description="群主ID")
    memberIds: List[str] = Field(default_factory=list, description="成员ID列表")

    # 状态
    status: int = Field(default=1, description="状态(1-正常, 2-已解散)")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000))
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000))

    class Settings:
        name = "group"
        indexes = [
            "name",
            "ownerId",
            "memberIds",  # 用于查询用户参与的群组
        ]
```

---

### 步骤 2: 创建请求 DTO

**文件**: `app/dto/group/group_request.py`

```python
"""群组请求 DTO"""
from typing import Optional, List
from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    """创建群组请求"""
    name: str = Field(..., min_length=1, max_length=50, description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    memberIds: List[str] = Field(..., min_length=1, description="初始成员ID列表")


class InviteMemberRequest(BaseModel):
    """邀请成员请求"""
    memberIds: List[str] = Field(..., min_length=1, description="要邀请的成员ID列表")


class RemoveMemberRequest(BaseModel):
    """移除成员请求"""
    memberId: str = Field(..., description="要移除的成员ID")


class UpdateGroupRequest(BaseModel):
    """修改群组信息请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")


class GroupListRequest(BaseModel):
    """群组列表请求"""
    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=20, ge=1, le=100, description="每页数量")
```

---

### 步骤 3: 创建响应 DTO

**文件**: `app/dto/group/group_response.py`

```python
"""群组响应 DTO"""
from typing import Optional, List
from pydantic import BaseModel, Field


class GroupMemberResponse(BaseModel):
    """群组成员响应"""
    userId: str = Field(..., description="用户ID")
    userName: str = Field(..., description="用户名")
    isOwner: bool = Field(default=False, description="是否为群主")


class GroupResponse(BaseModel):
    """群组详情响应"""
    id: str = Field(..., description="群组ID")
    name: str = Field(..., description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    ownerId: str = Field(..., description="群主ID")
    ownerName: str = Field(..., description="群主名称")
    memberIds: List[str] = Field(default_factory=list, description="成员ID列表")
    members: List[GroupMemberResponse] = Field(default_factory=list, description="成员详情列表")
    memberCount: int = Field(..., description="成员数量")
    status: int = Field(..., description="状态")
    createAt: int = Field(..., description="创建时间戳")
    updateAt: int = Field(..., description="更新时间戳")


class GroupListItemResponse(BaseModel):
    """群组列表项响应"""
    id: str = Field(..., description="群组ID")
    name: str = Field(..., description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    ownerId: str = Field(..., description="群主ID")
    ownerName: str = Field(..., description="群主名称")
    memberCount: int = Field(..., description="成员数量")
    status: int = Field(..., description="状态")
    createAt: int = Field(..., description="创建时间戳")


class GroupListResponse(BaseModel):
    """群组列表响应"""
    count: int = Field(..., description="总数")
    data: List[GroupListItemResponse] = Field(default_factory=list, description="群组列表")
```

---

### 步骤 4: 创建 Repository 层

**文件**: `app/repository/group_repository.py`

```python
"""群组数据访问层"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.group import Group

logger = logging.getLogger(__name__)


class GroupRepository:
    """群组数据访问层"""

    @staticmethod
    async def create(group: Group) -> Group:
        """创建群组"""
        await group.insert()
        logger.info(f"群组创建成功: id={group.id}, name={group.name}")
        return group

    @staticmethod
    async def find_by_id(group_id: str) -> Optional[Group]:
        """根据ID查询群组"""
        return await Group.get(PydanticObjectId(group_id))

    @staticmethod
    async def find_by_member_id(
        member_id: str,
        status: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Group], int]:
        """根据成员ID查询群组列表"""
        skip = (page - 1) * page_size
        conditions = [Group.memberIds == member_id]
        if status is not None:
            conditions.append(Group.status == status)

        query = Group.find(*conditions)
        total = await query.count()
        groups = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return groups, total

    @staticmethod
    async def update(group: Group) -> Group:
        """更新群组"""
        await group.save()
        logger.info(f"群组更新成功: id={group.id}")
        return group

    @staticmethod
    async def delete(group_id: str) -> bool:
        """删除群组"""
        group = await GroupRepository.find_by_id(group_id)
        if not group:
            return False
        await group.delete()
        logger.info(f"群组删除成功: id={group_id}")
        return True
```

---

### 步骤 5: 创建 Service 层

**文件**: `app/services/group_service.py`

需要实现的方法：
- `create()` - 创建群组
- `list()` - 获取群组列表
- `info()` - 获取群组详情
- `invite()` - 邀请成员
- `remove()` - 移除成员
- `exit()` - 退出群组
- `update()` - 修改群组信息
- `dismiss()` - 解散群组

**关键业务逻辑**:
1. 权限检查：`_check_is_owner()`
2. 成员数量限制：常量 `MAX_MEMBERS = 100`
3. 系统消息发送：通过 `ws_manager` 广播

---

### 步骤 6: 创建 Router 层

**文件**: `app/routers/group.py`

路由定义：
```python
router = APIRouter(prefix="/group", tags=["群组管理"])

@router.post("/create", ...)
@router.get("/list", ...)
@router.get("/{id}", ...)
@router.post("/{id}/invite", ...)
@router.post("/{id}/remove", ...)
@router.post("/{id}/exit", ...)
@router.put("/{id}", ...)
@router.delete("/{id}", ...)
```

---

### 步骤 7: 注册路由和模型

**修改**: `app/main.py`

```python
# 导入 Group 模型
from app.models.group import Group

# 在 init_beanie 中添加 Group
document_models=[
    User, Todo, Approval, Department, DepartmentUser, ChatLog,
    Group,  # 新增
]

# 注册路由
from app.routers import group as group_router
app.include_router(group_router.router, prefix=settings.API_PREFIX)
```

---

## 3. 常量定义

| 常量 | 值 | 说明 |
|------|-----|------|
| MAX_MEMBERS | 100 | 群组成员上限 |
| STATUS_NORMAL | 1 | 群组正常状态 |
| STATUS_DISMISSED | 2 | 群组已解散 |

---

## 4. 错误处理

| 场景 | 异常类型 | 错误信息 |
|------|----------|----------|
| 群组不存在 | ResourceNotFoundException | "群组不存在" |
| 无权限 | BusinessValidationException | "只有群主可以操作" |
| 成员已存在 | BusinessValidationException | "用户已在群组中" |
| 成员超限 | BusinessValidationException | "群组成员数量已达上限" |
| 群主退出 | BusinessValidationException | "群主不能退出群组" |
| 群组已解散 | BusinessValidationException | "群组已解散" |

---

## 5. WebSocket 系统消息格式

创建辅助方法 `_send_system_message()`：

```python
async def _send_system_message(
    group_id: str,
    system_type: str,
    content: str,
    group_info: Optional[dict] = None
):
    """发送群组系统消息"""
    # 构建系统消息
    # 通过 ws_manager.broadcast() 广播
```

系统消息类型：
- `group_create` - 群组创建
- `group_dismiss` - 群组解散
- `group_invite` - 成员邀请
- `group_remove` - 成员移除
- `group_exit` - 成员退出
