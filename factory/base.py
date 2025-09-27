"""
    工厂模式
"""
import abc
from collections.abc import Callable
from email.policy import strict
from enum import Enum
from typing import Generic, TypeVar, Type, Dict
from pydantic import BaseModel
from common import EFactory

T = TypeVar('T')

class Factory(abc.ABC, Generic[T]):

    @abc.abstractmethod
    def create(self, *args, **kwargs) -> T: raise NotImplementedError


class IFactory(Factory[T], Generic[T]):

    def __init__(
            self,
            factory: Type[T] | Callable[..., T]
    ):
        """
        初始化方法
        :param factory: 类型对象，可通过调用类型对象创建对应的实例对象
        """
        self.__factory = factory

    def create(
            self,
            *args,
            **kwargs
    ) -> T:
        """

        :param args: 创建实例对象需要的位置参数
        :param kwargs: 创建实例对象需要的关键字参数
        :return: 实例对象
        """
        # 如果实例对象是pydantic.BaseModel的子类，则通过model_validate进行创建
        if issubclass(self.__factory.__class__, BaseModel):
            return self.__factory.model_validate(kwargs)
        else:
            # 实例对象不是pydantic.BaseModel的子类，正常创建
            return self.__factory(*args, **kwargs)


class PoolFactory(Factory[T], abc.ABC, Generic[T]):

    __pool: Dict = {}

    def __new__(cls):
        # If the object exists in the pool - just return it
        obj = cls.__pool.get(cls.id())
        # otherwise - create new one (and add it to the pool)
        if obj is None:
            obj = object.__new__(cls)
            cls.__pool[cls.id()] = obj
        return obj

    @classmethod
    @abc.abstractmethod
    def id(cls) -> EFactory: raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def instance_pool(cls) -> Dict[Enum, Factory[T] | T]: raise NotImplementedError

    def create(self, e: Enum, *args, **kwargs) -> T:
        return self.instance_pool()[e].create(*args, **kwargs)
