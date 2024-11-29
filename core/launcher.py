import json
import signal
import logging
import configparser
from typing import Dict, List, Tuple
from logging.handlers import RotatingFileHandler

from tornado.ioloop import IOLoop
from tornado.web import Application
from apscheduler.triggers.cron import CronTrigger

from core import ReaderSection, LoggerSection, TemplatesDir
from core.exception import ReaderError
from core.router import router
from core.utils.scheduler import Scheduler
from core.utils.httpserver import HttpServer
from core.reader.reader import BaseReader, ReaderManager
from core.publisher.publisher import BasePublisher, PublisherManager


class Launcher:
    def __init__(self, **kwargs):
        self._scheduler = Scheduler()
        self._server: HttpServer = None
        self._logger: logging.Logger = None
        self._config: configparser.ConfigParser() = None
        self._flows: Dict[BaseReader, List[Tuple[str, BasePublisher]]] = {}  # 数据流，一个数据读取对应多个发布器 {读取器：[(时间: 发布器)]}

        self.init_config(kwargs.get("config"))
        self.initialize()

    def init_config(self, config_path: str):
        """初始化配置文件"""
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        self._config = config

    def initialize(self):
        """初始化配置"""
        self.init_logger()
        # 存在初始化顺序，先初始化httpserver给flow的publisher提供路由对象，scheduler再根据flow设置定时任务
        self.init_httpserver()
        self.init_flow()
        self.init_scheduler()

        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.stop())

    def init_logger(self):
        """初始化日志服务"""
        if not self._config.has_section(LoggerSection):
            raise ReaderError("Configuration file error, section {} not found".format(LoggerSection))

        logger = logging.getLogger()
        logger.setLevel(self._config.get(LoggerSection, "level").upper())
        formatter = logging.Formatter(self._config.get(LoggerSection, "formatter", raw=True))

        handler = logging.handlers.RotatingFileHandler(
            self._config.get(LoggerSection, "logfile"),
            maxBytes=self._config.getint(LoggerSection, "maxBytes"),
            backupCount=self._config.getint(LoggerSection, "backupCount"),
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # 屏蔽apscheduler调度器默认warning以下的日志
        scheduler_logger = logging.getLogger("apscheduler")
        scheduler_logger.setLevel(logging.WARNING)

        asyncio_logger = logging.getLogger("asyncio")
        asyncio_logger.setLevel(logging.WARNING)

        self._logger = logger

    def init_flow(self):
        """初始化数据流对象映射表"""
        if not self._config.has_section(ReaderSection):
            raise ReaderError("Configuration file error, section {} not found".format(ReaderSection))

        for _, config in self._config.items(ReaderSection):
            with (open(config, "r", encoding="utf-8") as f):
                data = json.loads(f.read())
                publishers = data.pop("publishers")
                reader = ReaderManager.get_reader(data.pop("name"), **data)

                self._flows[reader] = [(kwargs.pop("cron_expr"), PublisherManager.get_publisher(name, **kwargs)) for
                                       name, kwargs in publishers.items()]

    def init_scheduler(self):
        """初始化调度器"""
        for reader, publishers in self._flows.items():
            for cron_expr, publisher in publishers:
                self._scheduler.add_task(lambda r, p: p.publish(**r.read(need_title=True)),
                                         CronTrigger.from_crontab(cron_expr), args=[reader, publisher])
                self._logger.info(f"Scheduler add {publisher.name} started")

    def init_httpserver(self):
        """初始化http服务"""
        port, addr = self._config.getint("server", "port"), self._config.get("server", "address")
        app = Application(router, **{
            "template_path": TemplatesDir,
            "m_url": "{}://{}:{}".format(
                "https" if self._config.getboolean("server", "tls") else "http",
                self._config.get("server", "domain"),
                port
            ),
        })

        self._server = HttpServer(app)
        self._server.app = app
        self._server.listen(port, addr)
        self._logger.info(f"Server listen at {addr}:{port}")

    def start(self, ):
        """启动"""
        if self._server:
            self._server.start()
            self._logger.info("Server started")

        self._scheduler.start()
        self._logger.info("Scheduler started")

        IOLoop.current().start()

    def stop(self):
        """停止"""
        if self._server:
            self._server.stop()
            self._logger.info("Server stopped")

        self._scheduler.stop()
        self._logger.info("Scheduler stopped")

        IOLoop.current().stop()
        self._logger.info("IOLoop stopped")
        exit(0)
