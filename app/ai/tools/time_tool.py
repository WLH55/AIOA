"""
时间解析工具

提供自然语言时间表达式解析和当前时间获取功能
"""
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from langchain_core.tools import StructuredTool, BaseTool

from app.ai.tools.base import ToolProvider


# 东八区时区
_CST = timezone(timedelta(hours=8))


# 相对日期映射
_RELATIVE_DAYS = {
    "大后天": 3,
    "后天": 2,
    "明天": 1,
    "明日": 1,
    "今天": 0,
    "今日": 0,
}


# 时间段默认小时映射
_TIME_PERIODS = {
    "凌晨": 2,
    "早上": 8,
    "上午": 9,
    "中午": 12,
    "下午": 14,
    "傍晚": 17,
    "晚上": 19,
    "夜间": 21,
}


def _extract_hour_minute(remaining: str, periodHour: int = None) -> tuple:
    """
    从剩余文本中提取小时和分钟

    Args:
        remaining: 去掉日期/时段前缀后的文本
        periodHour: 时间段默认小时（如"下午"为14）

    Returns:
        (小时, 分钟) 元组
    """
    match = re.match(r"(\d{1,2})[:点](\d{1,2})?[分:]?(\d{1,2})?分?", remaining)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        if periodHour is not None and periodHour >= 12 and hour <= 12:
            if hour < 12:
                hour += 12
        return hour, minute
    return periodHour if periodHour else 0, 0


def _parse_expression(expression: str) -> str:
    """
    解析自然语言时间表达式

    Args:
        expression: 自然语言时间表达式

    Returns:
        格式化的结果字符串，如 "1743326400000 (2026-03-30 15:00:00)"
    """
    expr = expression.strip()
    now = datetime.now(_CST)

    # 1. 尝试标准格式: YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM
    match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$", expr)
    if match:
        try:
            second = int(match.group(6)) if match.group(6) else 0
            target = datetime(
                int(match.group(1)), int(match.group(2)), int(match.group(3)),
                int(match.group(4)), int(match.group(5)), second,
                tzinfo=_CST,
            )
            return _format_result(target)
        except ValueError:
            return f"无法解析时间表达式: {expression}"

    # 2. 尝试标准日期: YYYY-MM-DD
    match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})$", expr)
    if match:
        try:
            target = datetime(
                int(match.group(1)), int(match.group(2)), int(match.group(3)),
                tzinfo=_CST,
            )
            return _format_result(target)
        except ValueError:
            return f"无法解析时间表达式: {expression}"

    # 3. 尝试相对日期 + 时间组合
    for day_word, delta_days in _RELATIVE_DAYS.items():
        if expr.startswith(day_word):
            base_date = now + timedelta(days=delta_days)
            remaining = expr[len(day_word):].strip()
            if not remaining:
                target = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
                return _format_result(target)
            periodHour = None
            for period, ph in _TIME_PERIODS.items():
                if remaining.startswith(period):
                    periodHour = ph
                    remaining = remaining[len(period):].strip()
                    break
            hour, minute = _extract_hour_minute(remaining, periodHour)
            target = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return _format_result(target)

    # 4. 尝试时间段 + 时间
    for period, periodHour in _TIME_PERIODS.items():
        if expr.startswith(period):
            remaining = expr[len(period):].strip()
            if not remaining:
                target = now.replace(hour=periodHour, minute=0, second=0, microsecond=0)
                return _format_result(target)
            hour, minute = _extract_hour_minute(remaining, periodHour)
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return _format_result(target)

    # 5. 尝试纯时间
    hour, minute = _extract_hour_minute(expr)
    if hour > 0 or minute > 0:
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return _format_result(target)

    return f"无法解析时间表达式: {expression}"


def _format_result(target: datetime) -> str:
    """
    格式化解析结果

    Args:
        target: 目标时间

    Returns:
        格式化字符串
    """
    ts_ms = int(target.timestamp() * 1000)
    formatted = target.strftime("%Y-%m-%d %H:%M:%S")
    return f"{ts_ms} ({formatted})"


def _parse_time(expression: str) -> str:
    """
    将自然语言时间表达式转换为 Unix 时间戳（毫秒）

    Args:
        expression: 自然语言时间表达式

    Returns:
        时间戳（毫秒）和格式化日期时间字符串
    """
    return _parse_expression(expression)


def _get_current_time() -> str:
    """
    获取当前时间和时间戳

    Returns:
        当前时间信息
    """
    now = datetime.now(_CST)
    ts_ms = int(now.timestamp() * 1000)
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"当前时间：{formatted}，时间戳：{ts_ms}"


class TimeToolProvider(ToolProvider):
    """时间工具提供者"""

    name = "time"
    description = "时间解析工具"
    requires_context = False
    category = "utility"

    def get_tools(
        self,
        user_id: str = None,
        user_name: str = None,
        context: Dict[str, Any] = None,
    ) -> List[BaseTool]:
        """
        获取时间工具列表

        Args:
            user_id: 当前用户 ID（未使用）
            user_name: 当前用户名（未使用）
            context: 额外上下文信息（未使用）

        Returns:
            工具列表
        """
        return [
            StructuredTool.from_function(
                func=_parse_time,
                name="parseTime",
                description=(
                    "将自然语言时间表达式转换为 Unix 时间戳（毫秒）。"
                    "支持：今天、明天、后天、上午、下午、晚上、凌晨、9点、15:00、2024-01-15 09:00"
                ),
            ),
            StructuredTool.from_function(
                func=_get_current_time,
                name="getCurrentTime",
                description="获取当前时间和时间戳。",
            ),
        ]


# 模块导入时自动注册
TimeToolProvider().register()