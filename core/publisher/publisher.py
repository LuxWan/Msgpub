import logging
from abc import ABC
from typing import Type

from core.exception import NotFoundError


class BasePublisher(ABC):
    """数据发布器"""
    logger: logging.Logger = logging.getLogger(__name__)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.name = cls.__name__.removesuffix("Publisher").lower()

    def publish(self, *args, **kwargs):
        raise NotImplementedError


class PublisherManager:
    """发布器管理类"""

    @staticmethod
    def get_publisher_cls_by_name(name: str) -> Type[BasePublisher]:
        for c in BasePublisher.__subclasses__():
            if c.name == name:
                return c

        raise NotFoundError("Publisher with name '{}' not found".format(name))

    @classmethod
    def get_publisher(cls, name: str, **kwargs) -> BasePublisher:
        return cls.get_publisher_cls_by_name(name)(**kwargs)
