import abc
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Protocol, TypeVar, Generic, Iterable, Annotated, List
from filelock import FileLock, BaseFileLock
from pydantic import BaseModel, validate_call, FilePath, Field
from common import EModel, ERepoDatasource
from factory import IModelFactory

T = TypeVar('T', bound=BaseModel)
class PRepository(Protocol):

    def add(self, e: T | None): raise NotImplementedError

    def delete(self, e: T | None) -> int: raise NotImplementedError

    def update(self, c: T | None, e: T | None) -> int: raise NotImplementedError

    def query(self, e: T | None, limit: int) -> T | Iterable[T]: raise NotImplementedError


class Repository(abc.ABC, Generic[T]):
    @validate_call()
    def __init__(
            self,
            t: Annotated[
                EModel,
                Field(title='模型类型', default=EModel.APP_CONFIG)
            ]
    ):
        self.__t = t

    @property
    def t(self) -> EModel: return self.__t

    @abc.abstractmethod
    def add(self, e: T | None): raise NotImplementedError

    @abc.abstractmethod
    def delete(self, e: T | None) -> int: raise NotImplementedError

    @abc.abstractmethod
    def update(self, c: T | None, e: T | None) -> int: raise NotImplementedError

    @abc.abstractmethod
    def query(self, e: T | None, limit: int) -> None | T | Iterable[T]: raise NotImplementedError

class LocalFileRepository(Repository, abc.ABC, Generic[T]):
    @validate_call()
    def __init__(
            self,
            file: Annotated[
                FilePath,
                Field(title='文件路径')
            ],
            time_wait: Annotated[
                int,
                Field(title='抢锁等待时间', ge=0, default=5)
            ],
            t: Annotated[
                EModel,
                Field(title='模型类型', default=EModel.APP_CONFIG)
            ],
            memory: Annotated[
                bool,
                Field(title='数据是否导入内存', default=True)
            ]
    ):
        super().__init__(t)
        self.__file = file
        self.__lock = FileLock(
            '.'.join([str(self.__file), 'lock']),
            time_wait,
            blocking=True,
            is_singleton=True,
        )
        self.__memory = memory
        self.__data = self.load_data() if self.memory else self.load_data

    @property
    def file(self) -> Path: return self.__file

    @property
    def lock(self) -> BaseFileLock: return self.__lock

    @property
    def memory(self) -> bool: return self.__memory

    @property
    def data(self) -> None | T | Iterable[T]:
        return self.__data if self.memory else self.__data()


    @abc.abstractmethod
    def load_data(self) -> None | T | Iterable[T]: raise NotImplementedError

    @abc.abstractmethod
    def save_data(self, data: None | T | Iterable[T]) -> None:
        if self.memory:
            self.__data = self.load_data()

class JsonFileRepository(LocalFileRepository, abc.ABC, Generic[T]):

    def add(self, e: T | None):
        if e is None: return

        data: None | T | Iterable[T] = self.data
        if data is None or issubclass(data.__class__, BaseModel):
            self.save_data(e)
        else:
            self.save_data([*data, e])

    def delete(self, e: T | None) -> int:
        data: None | T | Iterable[T] = self.data

        if data is None or issubclass(data.__class__, BaseModel):
            self.save_data(None)
            return 1 if data else 0

        d: List[T] = []
        cnt: int = 0
        for item in data:
            c = item.model_dump(serialize_as_any=True)
            if e:
                c.update(e.model_dump(serialize_as_any=True, exclude_unset=True))
            i = item.model_dump(serialize_as_any=True)
            if c != i:
                d.append(item)
            else:
                cnt = cnt + 1
        self.save_data(d)
        return cnt

    def update(self, c: T | None, e: T | None) -> int:
        if e is None: return 0

        data: None | T | Iterable[T] = self.query(c, 0)
        if data is None or issubclass(data.__class__, BaseModel):
            if data is None:
                self.save_data(None)
                return 0
            d = data.model_dump(serialize_as_any=True)
            d.update(e.model_dump(serialize_as_any=True, exclude_unset=True))
            self.save_data(IModelFactory().create(self.t, **d))
            return 1

        results: List[T] = []
        for item in data:
            d = item.model_dump(serialize_as_any=True)
            d.update(e.model_dump(serialize_as_any=True, exclude_unset=True))
            results.append(IModelFactory().create(self.t, **d))
        self.save_data(results)
        return len(results)

    def query(self, e: T | None, limit: int = 0) -> None | T | Iterable[T]:
        data: None | T | Iterable[T] = self.data

        if data is None or issubclass(data.__class__, BaseModel):
            return data

        if e is None:
            if limit <= 0: return data
            else: return [item for index, item in data if index < limit]

        def __eq(condition: T, item: T) -> bool:
            _c = item.model_dump(serialize_as_any=True)
            _c.update(condition.model_dump(serialize_as_any=True, exclude_unset=True))
            return _c == item.model_dump(serialize_as_any=True)

        return [item for index, item in enumerate(data) if __eq(e, item) and (limit <= 0 or index < limit)]

    def load_data(self) -> None | T | Iterable[T]:
        with open(self.file, 'rt', encoding='utf8') as f:
            try:
                config = json.load(f)
            except JSONDecodeError:
                return None

        if isinstance(config, dict): return IModelFactory().create(self.t, **config)
        return [IModelFactory().create(self.t, **item) for item in config]


    def save_data(self, data: None | T | Iterable[T]) -> None:
        with self.lock:
            with open(self.file, 'wt', encoding='utf8') as f:
                if data is None:
                    f.write('{}')
                elif issubclass(data.__class__, BaseModel):
                    f.write(data.model_dump_json(serialize_as_any=True))
                else:
                    f.write('[')
                    f.writelines([
                        f'{item.model_dump_json(serialize_as_any=True)}{"" if index == 0 else ","}'
                        for index, item in enumerate(data)
                    ])
                    f.write(']')
            super().save_data(data)

class IRepository(Generic[T]):
    def __init__(
            self,
            repo_datasource: ERepoDatasource = ERepoDatasource.LOCAL_JSON_FILE,
            t: EModel = EModel.APP_CONFIG,
            *args,
            **kwargs
    ):
        kwargs.update({'t': t})

        match repo_datasource:
            case ERepoDatasource.LOCAL_JSON_FILE:
                self.__repo = JsonFileRepository[T](*args, **kwargs)
            case _:
                raise NotImplementedError

    def add(self, e: T | None):
        self.__repo.add(e)

    def delete(self, e: T | None) -> int:
        return self.__repo.delete(e)

    def update(self, c: T | None, e: T | None) -> int:
        return self.__repo.update(c, e)

    def query(self, e: T | None = None, limit: int = 0) -> None | T | Iterable[T]:
        return self.__repo.query(e, limit)