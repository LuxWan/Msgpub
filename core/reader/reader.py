import logging
from abc import ABC
from typing import Type, Tuple

from core.exception import NotFoundError


class BaseReader(ABC):
    """数据读取器"""
    logger: logging.Logger = logging.getLogger(__name__)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.name = cls.__name__.removesuffix("Reader").lower()

    def read(self, *args, **kwargs) -> Tuple:
        raise NotImplementedError

    @classmethod
    def initialize(cls, **kwargs):
        return cls(**kwargs)


class ReaderManager:
    """读取器管理类"""

    @staticmethod
    def get_reader_cls_by_name(name: str) -> Type[BaseReader]:
        for c in BaseReader.__subclasses__():
            if name.lower() == c.name:
                return c

        raise NotFoundError("Reader with name '{}' not found".format(name))

    @classmethod
    def get_reader(cls, name: str, **kwargs) -> BaseReader:
        return cls.get_reader_cls_by_name(name)(**kwargs)
