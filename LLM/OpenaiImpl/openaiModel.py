from abc import ABC
from Core.basicModel import BasicModel
from openai import OpenAI


class OpenaiModel(BasicModel, ABC):
    def __init__(self, model_name, model_url, api_key):
        super().__init__(model_name, model_url, api_key)
        self._model = OpenAI(
            base_url=self.model_url,
            api_key=self.api_key,
        )

    def invoke(self, *args, **kwargs):
        inputs = kwargs.get("messages", "")
        if isinstance(inputs, str):
            inputs = [
                {
                    "role": "user",
                    "content": inputs
                }
            ]

        elif isinstance(inputs, dict):
            inputs = [inputs]

        elif isinstance(inputs, list):
            inputs = inputs

        else:
            raise ValueError("Invalid inputs, only str or dict or list")

        response = self._model.chat.completions.create(
            model=self.model_name,
            messages=inputs,
            stream=False
        )

        return response.choices[0].message.content

