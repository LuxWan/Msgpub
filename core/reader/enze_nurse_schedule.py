from io import IOBase
from typing import Union, Dict, Tuple
from datetime import datetime, timedelta

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.utils.exceptions import InvalidFileException

from core.reader.reader import BaseReader
from core.utils.httpserver import HttpServer

ENZE_TITLE_TEMPLATE = "今日排班：{}"
ENZE_ERROR_TITLE_TEMPLATE = "今日({})排班暂未知"

ENZE_TEMPLATE = """今日排班：{}，明日排班：{}"""
ENZE_ERROR_TEMPLATE = """今日（{}）排班未更新或格式存在问题"""
ENZE_UPDATE_TEMPLATE = """请点击 {} 上传最新排班文件"""


class EnzeReader(BaseReader):
    def __init__(self, title_key: str, content_key: str, date_format: str, sheet: str = "Sheet1"):
        self._title_key = title_key
        self._content_key = content_key
        self._date_format = date_format
        self._sheet = sheet

        self._workbook: Workbook = None
        self._cur_schedule: Dict[str, str] = {}  # 当前排班映射表{日期：内容}  eg. {"11.8": "X"}
        self._next_schedule: Dict[str, str] = {}  # 下周排班映射表
        self._url = ""  # 文件上传地址

        self.init_server_handler()

    def init_server_handler(self):
        app = HttpServer().app
        app.settings[self.name] = self
        self._url = "{}/upload".format(app.settings.get("m_url", ""))

    def read(self, need_title: bool = False, **kwargs) -> Tuple:
        if need_title:
            return self.get_content(), self.get_title()
        return (self.get_content(),)

    def get_title(self):
        """获取标题"""
        today = datetime.now().strftime(self._date_format)
        if data := self._cur_schedule.get(today) or self._next_schedule.get(today):
            return ENZE_TITLE_TEMPLATE.format(data)
        return ENZE_ERROR_TITLE_TEMPLATE.format(today)

    def get_content(self):
        """获取内容"""
        today = datetime.now().strftime(self._date_format)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime(self._date_format)
        after_tomorrow = (datetime.now() + timedelta(days=2)).strftime(self._date_format)

        if not (today_schedule := self._cur_schedule.get(today)):
            # 已到第二周排班时间
            if today_schedule := self._next_schedule.get(today):
                self._cur_schedule = self._next_schedule.copy()
                self._next_schedule.clear()
            # 第二周排班未更新/未找到当前时间
            else:
                return ENZE_ERROR_TEMPLATE.format(today) + "，" + ENZE_UPDATE_TEMPLATE.format(self._url)

        tomorrow_schedule = self._cur_schedule.get(tomorrow) or self._next_schedule.get(tomorrow) or "未知"
        template = ENZE_TEMPLATE.format(today_schedule, tomorrow_schedule)
        # 提前两天提醒上传下周排班
        if not self._cur_schedule.get(after_tomorrow) and not self._next_schedule:
            template += "，" + ENZE_UPDATE_TEMPLATE.format(self._url)

        return template

    def handle(self, file: Union[str, IOBase]) -> bool:
        """提取Excel内容"""
        try:
            workbook = openpyxl.load_workbook(file)
        except InvalidFileException as e:
            self.logger.error("Load excel error {}".format(e))
            return False

        sheet = workbook[self._sheet]
        title = None
        data = None
        for content in sheet.values:
            if self._title_key in content:
                title = content
            if self._content_key in content:
                data = content

        for i in range(len(data)):
            if not title[i]:
                continue
            self._next_schedule[str(title[i])] = data[i]

        self._next_schedule = {str(title[i]): data[i] for i in range(len(data)) if title[i]}
        self.logger.info("Update schedule by {}, get data: {}".format(file, self._next_schedule))
        return True
