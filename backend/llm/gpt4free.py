from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatResult, ChatGenerationChunk, ChatGeneration
from pydantic import PrivateAttr, Field
from g4f.client import Client
from typing import List, AsyncGenerator, Any, Union
import asyncio


class GPT4Free(BaseChatModel):
    model: str = Field(...)
    temperature: float = 0.7

    _client: Client = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._client = Client()

    def _convert_messages_to_g4f_format(self, messages: List[BaseMessage]) -> List[dict]:
        """Convert LangChain messages to G4F format"""
        g4f_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                g4f_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                g4f_messages.append({"role": "assistant", "content": message.content})
            else:
                # Handle other message types as user messages
                g4f_messages.append({"role": "user", "content": message.content})
        return g4f_messages

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: List[str] = None,
            **kwargs,
    ) -> ChatResult:
        g4f_messages = self._convert_messages_to_g4f_format(messages)

        response = self._client.chat.completions.create(
            model=self.model,
            messages=g4f_messages,
            temperature=self.temperature,
            web_search=False,
        )

        message = response.choices[0].message.content
        # Добавляем перенос строки в конце сообщения
        if message and not message.endswith('\n'):
            message += '\n'
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=message))]
        )

    async def _agenerate(
            self,
            messages: List[BaseMessage],
            stop: List[str] = None,
            **kwargs,
    ) -> ChatResult:
        """Asynchronous generation method"""
        # Run the synchronous method in a thread pool
        return await asyncio.get_event_loop().run_in_executor(
            None, self._generate, messages, stop
        )

    async def _astream(
            self,
            messages: List[BaseMessage],
            stop: List[str] = None,
            **kwargs,
    ) -> AsyncGenerator[ChatGenerationChunk, None]:
        g4f_messages = self._convert_messages_to_g4f_format(messages)

        # Запуск стрима
        try:
            # Используем синхронный вызов, но оборачиваем его в async generator
            response = self._client.chat.completions.create(
                model=self.model,
                messages=g4f_messages,
                temperature=self.temperature,
                web_search=False,
                stream=True,
            )

            last_chunk_yielded = False
            for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        # Возвращаем по стандарту LangChain: AIMessageChunk → ChatGenerationChunk
                        yield ChatGenerationChunk(message=AIMessageChunk(content=delta.content))
                        last_chunk_yielded = True
                        # Добавляем небольшую задержку для лучшего стриминга

            # Добавляем перенос строки в конце сообщения
            if last_chunk_yielded:
                yield ChatGenerationChunk(message=AIMessageChunk(content='\n'))

        except Exception as e:
            # Fallback to non-streaming if streaming fails
            print(f"Streaming failed, falling back to non-streaming: {e}")
            result = await self._agenerate(messages, stop, **kwargs)
            content = result.generations[0].message.content
            # Simulate streaming by yielding word by word
            words = content.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield ChatGenerationChunk(message=AIMessageChunk(content=word))
                else:
                    yield ChatGenerationChunk(message=AIMessageChunk(content=" " + word))
            # Добавляем перенос строки в конце fallback сообщения
            yield ChatGenerationChunk(message=AIMessageChunk(content='\n'))

    def _stream(
            self,
            messages: List[BaseMessage],
            stop: List[str] = None,
            **kwargs,
    ):
        """Синхронный метод стриминга для совместимости"""
        g4f_messages = self._convert_messages_to_g4f_format(messages)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=g4f_messages,
                temperature=self.temperature,
                web_search=False,
                stream=True,
            )

            last_chunk_yielded = False
            for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield ChatGenerationChunk(message=AIMessageChunk(content=delta.content))
                        last_chunk_yielded = True

            # Добавляем перенос строки в конце сообщения
            if last_chunk_yielded:
                yield ChatGenerationChunk(message=AIMessageChunk(content='\n'))

        except Exception as e:
            print(f"Sync streaming failed, falling back to non-streaming: {e}")
            result = self._generate(messages, stop, **kwargs)
            content = result.generations[0].message.content
            # Simulate streaming by yielding the entire content at once
            yield ChatGenerationChunk(message=AIMessageChunk(content=content))

    @property
    def _llm_type(self) -> str:
        return "gpt4free"