"""
日志配置模块
"""
import gzip
import logging
import logging.handlers
import os
import shutil
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.config.settings import settings


class SizeTimeRotatingFileHandler(TimedRotatingFileHandler):
    """
    支持大小和时间双重轮转的日志处理器

    - 按时间轮转：每天午夜自动轮转
    - 按大小轮转：单个文件超过 maxBytes 时立即轮转
    """

    def __init__(self, filename, maxBytes=50*1024*1024, **kwargs):
        """
        初始化处理器

        Args:
            filename: 日志文件路径
            maxBytes: 单个日志文件最大字节数，默认 50MB
            **kwargs: 传递给 TimedRotatingFileHandler 的其他参数
        """
        self.maxBytes = maxBytes
        super().__init__(filename, **kwargs)

    def shouldRollover(self, record):
        """
        判断是否需要轮转

        时间轮转 OR 文件大小超过限制时触发轮转

        Args:
            record: 日志记录

        Returns:
            int: 0 表示不需要轮转，非 0 表示需要轮转
        """
        # 先检查时间轮转
        time_rollover = super().shouldRollover(record)
        # 再检查大小轮转
        if self.stream is None:
            self.stream = self._open()
        try:
            size_rollover = os.path.getsize(self.baseFilename) >= self.maxBytes
        except OSError:
            size_rollover = False
        return time_rollover or size_rollover

    def doRollover(self):
        """
        执行日志轮转

        重写以支持压缩旧日志
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # 获取当前时间作为后缀
        current_time = time.time()
        time_tuple = time.localtime(current_time)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple) + ".gz"
        # 如果目标文件已存在，添加序号
        if os.path.exists(dfn):
            base_dfn = dfn
            i = 1
            while os.path.exists(dfn):
                dfn = f"{base_dfn}.{i}"
                i += 1
        # 压缩当前日志文件
        if os.path.exists(self.baseFilename):
            try:
                with open(self.baseFilename, "rb") as f_in:
                    with gzip.open(dfn, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(self.baseFilename)
            except Exception:
                pass
        # 创建新的日志文件
        self.stream = self._open()
        # 清理旧的日志文件
        self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        """清理超过保留天数的日志文件"""
        current_time = time.time()
        cutoff_time = current_time - (self.backupCount * 86400)
        for log_file in Path(self.baseFilename).parent.glob("*.gz"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
            except (FileNotFoundError, Exception):
                pass


def setup_logging():
    """
    配置日志系统

    特性：
    - 按日期轮转日志文件（每天午夜）
    - 按大小轮转（单个文件最大 50MB）
    - 自动压缩旧日志为 .gz 格式
    - 自动清理超过 LOG_RETENTION_DAYS 的日志
    """
    # 确保日志目录存在
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    # 创建日志格式
    log_format = "[%(asctime)s] %(levelname)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    # 创建 formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.LOG_LEVEL)
    # 文件处理器（按时间+大小双重轮转）
    log_file = settings.LOGS_DIR / "app.log"
    file_handler = SizeTimeRotatingFileHandler(
        filename=str(log_file),
        maxBytes=50 * 1024 * 1024,  # 50MB
        when="midnight",
        interval=1,
        backupCount=settings.LOG_RETENTION_DAYS,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.LOG_LEVEL)
    # 配置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)