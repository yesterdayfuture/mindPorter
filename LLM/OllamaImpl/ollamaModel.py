from abc import ABC
from Core.basicModel import BasicModel
import ollama


class OllamaModel(BasicModel, ABC):
    def __init__(self, model_name, model_url, api_key):
        super().__init__(model_name, model_url, api_key)
        self._model = ollama.Client(
            host=model_url
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

        response = ollama.chat(
            model=self.model_name,
            messages=inputs,
            stream=False
        )

        return response['message']['content']

