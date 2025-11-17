from abc import ABC, abstractmethod
from typing import List, Optional


class BasicModel(ABC):

    # 子类信息存储
    _registered_models = {}

    def __init__(self, model_name: Optional[str] = None, model_url: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name
        self.model_url = model_url
        self.api_key = api_key

    # 自动将 子类 注册到 _registered_models 中
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class_name = cls.__name__.lower()

        BasicModel._registered_models[class_name] = cls

    @classmethod
    def createModel(cls, *args, **kwargs):
        class_name = kwargs.get('class_name', None)

        if class_name is None:
            raise KeyError('Class name must be provided')

        class_name = class_name.value

        model_name = kwargs.get('model_name', None)
        model_url = kwargs.get('model_url', None)
        api_key = kwargs.get('api_key', None)

        if class_name not in cls._registered_models:
            raise KeyError(f'Class name {class_name} is not registered')

        model = cls._registered_models[class_name](model_name, model_url, api_key)
        return model

    @abstractmethod
    def invoke(self, *args, **kwargs):
        raise KeyError('Method not implemented')


