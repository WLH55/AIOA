"""
AI 工具单元测试

覆盖时间工具、待办工具、审批工具、用户查询工具、部门查询工具
"""
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.ai.tools.time_tool import parseTime, getCurrentTime, _parse_expression
from app.ai.tools.user_tool import _get_user_by_name, get_user_tool
from app.ai.tools.department_tool import _get_department_tree, _get_department_info, get_department_tools


# ==================== 时间工具测试 ====================


class TestTimeParserTool:
    """TC-1.1 时间工具测试"""

    def test_parse_relative_date_tomorrow(self):
        """TC-1.1.1: 解析明天返回明天 0 点的时间戳"""
        cst = timezone(timedelta(hours=8))
        now = datetime.now(cst)
        tomorrow = now + timedelta(days=1)
        expected_date = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

        result = _parse_expression("明天")

        assert "无法解析" not in result
        ts_str = result.split(" ")[0]
        ts = int(ts_str)
        expected_ts = int(expected_date.timestamp() * 1000)
        assert abs(ts - expected_ts) < 1000

    def test_parse_relative_date_tomorrow_with_time(self):
        """TC-1.1.2: 解析明天下午3点返回明天 15:00 的时间戳"""
        cst = timezone(timedelta(hours=8))
        now = datetime.now(cst)
        tomorrow = now + timedelta(days=1)
        expected_date = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)

        result = _parse_expression("明天下午3点")

        assert "无法解析" not in result
        ts_str = result.split(" ")[0]
        ts = int(ts_str)
        expected_ts = int(expected_date.timestamp() * 1000)
        assert abs(ts - expected_ts) < 1000

    def test_parse_standard_format(self):
        """TC-1.1.3: 解析标准格式 2026-03-30 09:00"""
        result = _parse_expression("2026-03-30 09:00")

        assert "无法解析" not in result
        assert "2026-03-30 09:00:00" in result
        # 验证时间戳是毫秒级数字
        parts = result.split(" ")
        assert parts[0].isdigit()
        assert len(parts[0]) == 13

    def test_parse_relative_date_day_after_tomorrow(self):
        """TC-1.1.4: 解析后天返回后天 0 点的时间戳"""
        cst = timezone(timedelta(hours=8))
        now = datetime.now(cst)
        day_after = now + timedelta(days=2)
        expected_date = day_after.replace(hour=0, minute=0, second=0, microsecond=0)

        result = _parse_expression("后天")

        assert "无法解析" not in result
        ts_str = result.split(" ")[0]
        ts = int(ts_str)
        expected_ts = int(expected_date.timestamp() * 1000)
        assert abs(ts - expected_ts) < 1000

    def test_parse_invalid_expression(self):
        """TC-1.1.5: 无效表达式返回错误提示"""
        result = _parse_expression("abcxyz")

        assert "无法解析" in result

    def test_get_current_time(self):
        """TC-1.1.6: 获取当前时间返回时间戳和格式化字符串"""
        result = getCurrentTime.invoke({})

        assert "当前时间" in result
        assert "时间戳" in result
        assert datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d") in result

    def test_parse_today(self):
        """补充：解析相对日期 - 今天"""
        result = _parse_expression("今天")

        assert "无法解析" not in result
        assert "00:00:00" in result

    def test_parse_date_only(self):
        """补充：解析标准日期 YYYY-MM-DD"""
        result = _parse_expression("2026-01-15")

        assert "无法解析" not in result
        assert "2026-01-15" in result


# ==================== 待办工具测试 ====================


class TestTodoTools:
    """TC-1.2 待办工具测试"""

    @pytest.mark.asyncio
    async def test_create_todo_with_user_id(self):
        """TC-1.2.1: 创建待办（指定执行人ID）"""
        fake_user_id = "67e1" + "0" * 20
        mock_saved = MagicMock()
        mock_saved.id = "todo_id_abc123"
        mock_saved.executes = []
        mock_saved.save = AsyncMock()

        with patch("app.ai.tools.todo_tool.Todo", return_value=mock_saved) as MockTodo, \
             patch("app.ai.tools.todo_tool.UserTodo", return_value=MagicMock()), \
             patch("app.ai.tools.todo_tool.TodoRepository") as mock_repo, \
             patch("app.ai.tools.todo_tool.UserRepository") as mock_user_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)
            mock_user = MagicMock()
            mock_user.id = fake_user_id
            mock_user.name = "用户A"
            mock_user_repo.find_by_ids = AsyncMock(return_value=[mock_user])

            from app.ai.tools.todo_tool import _make_create_todo
            create_fn = _make_create_todo("user123", "测试用户")
            result = await create_fn(title="完成报告", executorNames=[fake_user_id])

            assert "待办创建成功" in result
            assert "完成报告" in result

    @pytest.mark.asyncio
    async def test_create_todo_with_user_name(self):
        """TC-1.2.2: 创建待办（指定用户名）自动转换"""
        mock_saved = MagicMock()
        mock_saved.id = "todo_id_abc123"
        mock_saved.executes = []
        mock_saved.save = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user_id_456"
        mock_user.name = "张三"

        with patch("app.ai.tools.todo_tool.Todo", return_value=mock_saved), \
             patch("app.ai.tools.todo_tool.UserTodo", return_value=MagicMock()), \
             patch("app.ai.tools.todo_tool.TodoRepository") as mock_repo, \
             patch("app.ai.tools.todo_tool.UserRepository") as mock_user_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)
            mock_user_repo.find_by_name = AsyncMock(return_value=mock_user)

            from app.ai.tools.todo_tool import _make_create_todo
            create_fn = _make_create_todo("user123", "测试用户")
            result = await create_fn(title="完成报告", executorNames=["张三"])

            assert "待办创建成功" in result
            mock_user_repo.find_by_name.assert_called_once_with("张三")

    @pytest.mark.asyncio
    async def test_create_todo_default_executor(self):
        """TC-1.2.3: 创建待办（不指定执行人）默认为当前用户"""
        mock_saved = MagicMock()
        mock_saved.id = "todo_id_abc123"
        mock_saved.executes = []
        mock_saved.save = AsyncMock()

        with patch("app.ai.tools.todo_tool.Todo", return_value=mock_saved), \
             patch("app.ai.tools.todo_tool.UserTodo", return_value=MagicMock()), \
             patch("app.ai.tools.todo_tool.TodoRepository") as mock_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)

            from app.ai.tools.todo_tool import _make_create_todo
            create_fn = _make_create_todo("user123", "测试用户")
            result = await create_fn(title="完成报告")

            assert "待办创建成功" in result
            assert "测试用户" in result

    @pytest.mark.asyncio
    async def test_create_todo_user_not_found(self):
        """TC-1.2 补充：创建待办指定不存在的用户名"""
        with patch("app.ai.tools.todo_tool.UserRepository") as mock_user_repo:
            mock_user_repo.find_by_name = AsyncMock(return_value=None)

            from app.ai.tools.todo_tool import _make_create_todo
            create_fn = _make_create_todo("user123", "测试用户")
            result = await create_fn(title="完成报告", executorNames=["不存在的用户"])

            assert "未找到用户" in result

    @pytest.mark.asyncio
    async def test_find_todos(self):
        """TC-1.2.4: 查询待办返回格式化列表"""
        mock_todo = MagicMock()
        mock_todo.title = "测试待办"
        mock_todo.todoStatus = 1
        mock_todo.deadlineAt = None

        with patch("app.ai.tools.todo_tool.TodoRepository") as mock_repo:
            mock_repo.find_by_execute_user_id = AsyncMock(return_value=([mock_todo], 1))

            from app.ai.tools.todo_tool import _make_find_todos
            find_fn = _make_find_todos("user123", "测试用户")
            result = await find_fn()

            assert "找到 1 条待办" in result
            assert "测试待办" in result

    @pytest.mark.asyncio
    async def test_find_todos_empty(self):
        """TC-1.2 补充：查询无待办"""
        with patch("app.ai.tools.todo_tool.TodoRepository") as mock_repo:
            mock_repo.find_by_execute_user_id = AsyncMock(return_value=([], 0))

            from app.ai.tools.todo_tool import _make_find_todos
            find_fn = _make_find_todos("user123", "测试用户")
            result = await find_fn()

            assert "暂无待办事项" in result

    def test_get_todo_tools_returns_list(self):
        """补充：get_todo_tools 返回正确的工具列表"""
        from app.ai.tools.todo_tool import get_todo_tools
        tools = get_todo_tools("user123", "测试用户")
        assert len(tools) == 2
        assert tools[0].name == "createTodo"
        assert tools[1].name == "findTodos"


# ==================== 审批工具测试 ====================


class TestApprovalTools:
    """TC-1.3 审批工具测试"""

    def test_generate_approval_no(self):
        """补充：审批编号格式正确"""
        from app.ai.tools.approval_tool import _generate_approval_no
        no = _generate_approval_no()
        assert no.startswith("AP")
        assert len(no) > 10

    @pytest.mark.asyncio
    async def test_create_leave_approval_sick(self):
        """TC-1.3.1: 创建病假审批"""
        mock_saved = MagicMock()
        mock_saved.no = "AP20260331001"

        with patch("app.ai.tools.approval_tool.Approval", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.Leave", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)

            from app.ai.tools.approval_tool import _make_create_leave_approval
            create_fn = _make_create_leave_approval("user123", "测试用户")
            now_ms = int(time.time() * 1000)
            result = await create_fn(
                leaveType=3,
                startTime=str(now_ms),
                endTime=str(now_ms + 86400000),
                reason="身体不适",
            )

            assert "请假申请已提交" in result
            assert "病假" in result

    @pytest.mark.asyncio
    async def test_create_leave_approval_annual(self):
        """TC-1.3.2: 创建年假审批"""
        mock_saved = MagicMock()
        mock_saved.no = "AP20260331002"

        with patch("app.ai.tools.approval_tool.Approval", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.Leave", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)

            from app.ai.tools.approval_tool import _make_create_leave_approval
            create_fn = _make_create_leave_approval("user123", "测试用户")
            now_ms = int(time.time() * 1000)
            result = await create_fn(
                leaveType=4,
                startTime=str(now_ms),
                endTime=str(now_ms + 172800000),
                reason="年假休息",
            )

            assert "请假申请已提交" in result
            assert "年假" in result

    @pytest.mark.asyncio
    async def test_create_punch_approval(self):
        """TC-1.3.3: 创建补卡审批"""
        mock_saved = MagicMock()
        mock_saved.no = "AP20260331003"

        with patch("app.ai.tools.approval_tool.Approval", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.MakeCard", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)

            from app.ai.tools.approval_tool import _make_create_punch_approval
            create_fn = _make_create_punch_approval("user123", "测试用户")
            now_ms = int(time.time() * 1000)
            result = await create_fn(
                punchType=1,
                date=str(now_ms),
                reason="忘记打卡",
            )

            assert "补卡申请已提交" in result
            assert "上班卡" in result

    @pytest.mark.asyncio
    async def test_create_go_out_approval(self):
        """TC-1.3.4: 创建外出审批"""
        mock_saved = MagicMock()
        mock_saved.no = "AP20260331004"

        with patch("app.ai.tools.approval_tool.Approval", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.GoOut", return_value=MagicMock()), \
             patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.create = AsyncMock(return_value=mock_saved)

            from app.ai.tools.approval_tool import _make_create_go_out_approval
            create_fn = _make_create_go_out_approval("user123", "测试用户")
            now_ms = int(time.time() * 1000)
            result = await create_fn(
                startTime=str(now_ms),
                endTime=str(now_ms + 3600000),
                reason="外出办事",
            )

            assert "外出申请已提交" in result

    @pytest.mark.asyncio
    async def test_find_approvals_mine(self):
        """TC-1.3.5: 查询我提交的审批"""
        mock_approval = MagicMock()
        mock_approval.status = 0
        mock_approval.type = 2
        mock_approval.title = "测试用户的病假申请"
        mock_approval.no = "AP20260331001"

        with patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.find_by_user_id = AsyncMock(return_value=([mock_approval], 1))

            from app.ai.tools.approval_tool import _make_find_approvals
            find_fn = _make_find_approvals("user123", "测试用户")
            result = await find_fn(queryType="mine")

            assert "找到 1 条" in result
            assert "我提交的" in result

    @pytest.mark.asyncio
    async def test_find_approvals_pending(self):
        """TC-1.3.6: 查询待我审批的"""
        mock_approval = MagicMock()
        mock_approval.status = 0
        mock_approval.type = 2
        mock_approval.title = "其他人的请假"
        mock_approval.no = "AP20260331005"

        with patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.find_by_approval_id_and_status = AsyncMock(
                return_value=([mock_approval], 1),
            )

            from app.ai.tools.approval_tool import _make_find_approvals
            find_fn = _make_find_approvals("user123", "测试用户")
            result = await find_fn(queryType="pending")

            assert "找到 1 条" in result
            assert "待我审批" in result

    @pytest.mark.asyncio
    async def test_create_leave_invalid_type(self):
        """TC-1.3.7: 无效请假类型"""
        from app.ai.tools.approval_tool import _make_create_leave_approval
        create_fn = _make_create_leave_approval("user123", "测试用户")
        result = await create_fn(
            leaveType=99,
            startTime="1743296400000",
            endTime="1743382800000",
            reason="测试",
        )

        assert "无效的请假类型" in result

    @pytest.mark.asyncio
    async def test_create_leave_end_before_start(self):
        """补充：结束时间早于开始时间"""
        from app.ai.tools.approval_tool import _make_create_leave_approval
        create_fn = _make_create_leave_approval("user123", "测试用户")
        result = await create_fn(
            leaveType=3,
            startTime="1743382800000",
            endTime="1743296400000",
            reason="测试",
        )

        assert "结束时间必须大于开始时间" in result

    @pytest.mark.asyncio
    async def test_create_punch_invalid_type(self):
        """补充：无效补卡类型"""
        from app.ai.tools.approval_tool import _make_create_punch_approval
        create_fn = _make_create_punch_approval("user123", "测试用户")
        result = await create_fn(
            punchType=3,
            date="1743296400000",
            reason="测试",
        )

        assert "无效的补卡类型" in result

    @pytest.mark.asyncio
    async def test_find_approvals_empty(self):
        """补充：无审批记录"""
        with patch("app.ai.tools.approval_tool.ApprovalRepository") as mock_repo:
            mock_repo.find_by_user_id = AsyncMock(return_value=([], 0))

            from app.ai.tools.approval_tool import _make_find_approvals
            find_fn = _make_find_approvals("user123", "测试用户")
            result = await find_fn(queryType="mine")

            assert "暂无" in result

    def test_get_approval_tools_returns_list(self):
        """补充：get_approval_tools 返回正确的工具列表"""
        from app.ai.tools.approval_tool import get_approval_tools
        tools = get_approval_tools("user123", "测试用户")
        names = [t.name for t in tools]
        assert "createLeaveApproval" in names
        assert "createPunchApproval" in names
        assert "createGoOutApproval" in names
        assert "findApprovals" in names


# ==================== 用户查询工具测试 ====================


class TestUserQueryTool:
    """TC-1.4 用户查询工具测试"""

    @pytest.mark.asyncio
    async def test_find_user_by_name(self):
        """TC-1.4.1: 按姓名查询用户"""
        mock_user = MagicMock()
        mock_user.name = "张三"
        mock_user.id = MagicMock()
        mock_user.id.__str__ = MagicMock(return_value="user_id_123")

        with patch("app.ai.tools.user_tool.UserRepository") as mock_repo:
            mock_repo.find_by_name = AsyncMock(return_value=mock_user)

            result = await _get_user_by_name("张三")

            assert "找到用户" in result
            assert "张三" in result

    @pytest.mark.asyncio
    async def test_find_user_not_found(self):
        """TC-1.4.2: 查询不存在的用户"""
        with patch("app.ai.tools.user_tool.UserRepository") as mock_repo:
            mock_repo.find_by_name = AsyncMock(return_value=None)

            result = await _get_user_by_name("不存在的用户")

            assert "未找到用户" in result

    def test_get_user_tool_returns_list(self):
        """补充：get_user_tool 返回工具列表"""
        tools = get_user_tool()
        assert len(tools) == 1
        assert tools[0].name == "getUserByName"


# ==================== 部门查询工具测试 ====================


class TestDepartmentTools:
    """TC-1.5 部门查询工具测试"""

    @pytest.mark.asyncio
    async def test_get_department_tree(self):
        """TC-1.5.1: 获取部门树"""
        mock_dept = MagicMock()
        mock_dept.id = MagicMock()
        mock_dept.id.__str__ = MagicMock(return_value="dept_001")
        mock_dept.name = "技术部"
        mock_dept.parentId = None
        mock_dept.level = 1

        with patch("app.ai.tools.department_tool.DepartmentRepository") as mock_repo:
            mock_repo.find_all = AsyncMock(return_value=[mock_dept])

            result = await _get_department_tree()

            assert "部门结构" in result
            assert "技术部" in result

    @pytest.mark.asyncio
    async def test_get_department_info(self):
        """TC-1.5.2: 获取部门详情"""
        mock_dept = MagicMock()
        mock_dept.id = MagicMock()
        mock_dept.id.__str__ = MagicMock(return_value="dept_001")
        mock_dept.name = "技术部"
        mock_dept.level = 1
        mock_dept.parentId = None

        with patch("app.ai.tools.department_tool.DepartmentRepository") as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=mock_dept)

            result = await _get_department_info("dept_001")

            assert "部门详情" in result
            assert "技术部" in result

    @pytest.mark.asyncio
    async def test_get_department_not_found(self):
        """TC-1.5.3: 获取不存在的部门"""
        with patch("app.ai.tools.department_tool.DepartmentRepository") as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=None)

            result = await _get_department_info("invalid_id")

            assert "未找到部门" in result

    @pytest.mark.asyncio
    async def test_get_department_tree_empty(self):
        """补充：空部门数据"""
        with patch("app.ai.tools.department_tool.DepartmentRepository") as mock_repo:
            mock_repo.find_all = AsyncMock(return_value=[])

            result = await _get_department_tree()

            assert "暂无部门数据" in result

    @pytest.mark.asyncio
    async def test_get_department_info_empty_id_returns_tree(self):
        """补充：空 departmentId 返回部门树"""
        with patch("app.ai.tools.department_tool.DepartmentRepository") as mock_repo:
            mock_repo.find_all = AsyncMock(return_value=[])

            result = await _get_department_info("")

            assert "暂无部门数据" in result

    def test_get_department_tools_returns_list(self):
        """补充：get_department_tools 返回工具列表"""
        tools = get_department_tools()
        names = [t.name for t in tools]
        assert "getDepartmentTree" in names
        assert "getDepartmentInfo" in names


# ==================== 工具注册中心测试 ====================


class TestToolRegistry:
    """工具注册中心测试"""

    def test_get_all_tools_returns_expected_tools(self):
        """补充：get_all_tools 返回全部预期工具"""
        from app.ai.tools.registry import get_all_tools
        tools = get_all_tools("user123", "测试用户")
        names = [t.name for t in tools]

        expected = [
            "parseTime", "getCurrentTime", "getUserByName",
            "getDepartmentTree", "getDepartmentInfo",
            "createTodo", "findTodos",
            "createLeaveApproval", "createPunchApproval",
            "createGoOutApproval", "findApprovals",
        ]
        assert len(tools) == len(expected)
        for name in expected:
            assert name in names, f"缺少工具: {name}"
