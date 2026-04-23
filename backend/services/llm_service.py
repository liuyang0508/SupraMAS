"""
LLM Service - Unified LLM client for all agents
Provides OpenAI, Anthropic, vLLM support with retry, fallback, and streaming
"""

import os
import logging
from typing import Optional, List, Dict, Any, AsyncIterator
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM响应结构"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class LLMService:
    """
    Unified LLM Service

    Features:
    - Multi-provider: OpenAI, Anthropic, MiniMax
    - Automatic retry with exponential backoff
    - Streaming support
    - Token counting and cost estimation
    """

    def __init__(self):
        self._client = None
        self._provider = None
        self._initialized = False
        self._init_client()

    def _init_client(self):
        """Initialize LLM client based on configuration"""
        from config.settings import config as app_config
        llm_cfg = app_config.llm

        api_key = llm_cfg.OPENAI_API_KEY
        if not api_key or api_key == "your-openai-api-key-here":
            logger.warning("[LLMService] No API key configured, LLM calls will use mock responses")
            return

        base_url = llm_cfg.OPENAI_BASE_URL
        provider = llm_cfg.LLM_PROVIDER

        try:
            if "minimax" in (base_url or "").lower():
                # MiniMax Anthropic-compatible API
                self._provider = "minimax"
                self._base_url = base_url.rstrip("/")
                self._api_key = api_key
                self._model = llm_cfg.OPENAI_MODEL
                self._initialized = True
                logger.info(f"[LLMService] Initialized MiniMax client with model {self._model}")

            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                self._client = ChatOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    model=llm_cfg.OPENAI_MODEL,
                    temperature=llm_cfg.TEMPERATURE,
                    max_tokens=llm_cfg.MAX_TOKENS,
                    streaming=llm_cfg.STREAMING
                )
                self._provider = "openai"
                self._initialized = True
                logger.info(f"[LLMService] Initialized OpenAI client with model {llm_cfg.OPENAI_MODEL}")

            elif provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self._client = ChatAnthropic(
                    api_key=api_key,
                    model="claude-3-sonnet-20240229",
                    temperature=llm_cfg.TEMPERATURE,
                    max_tokens=llm_cfg.MAX_TOKENS
                )
                self._provider = "anthropic"
                self._initialized = True
                logger.info("[LLMService] Initialized Anthropic client")

            elif provider == "vllm":
                from langchain_openai import ChatOpenAI
                self._client = ChatOpenAI(
                    api_key="not-needed",
                    base_url=llm_cfg.VLLM_BASE_URL,
                    model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                    temperature=llm_cfg.TEMPERATURE,
                    max_tokens=llm_cfg.MAX_TOKENS
                )
                self._provider = "vllm"
                self._initialized = True
                logger.info(f"[LLMService] Initialized vLLM client")

        except ImportError as e:
            logger.error(f"[LLMService] Required package not installed: {e}")
        except Exception as e:
            logger.error(f"[LLMService] Failed to initialize: {e}")

    @property
    def is_available(self) -> bool:
        return self._initialized

    @property
    def provider(self) -> str:
        return self._provider or "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text from LLM"""
        if not self._initialized:
            return self._mock_response(prompt)

        if self._provider == "minimax":
            return await self._generate_minimax(prompt, system_prompt, temperature, max_tokens)

        if self._client:
            return await self._generate_langchain(prompt, system_prompt, temperature, max_tokens, stop_sequences, **kwargs)

        return self._mock_response(prompt)

    async def _generate_minimax(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate using MiniMax Anthropic-compatible API"""
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "user", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self._model,
            "max_tokens": max_tokens or 4096,
            "messages": messages
        }

        if temperature is not None:
            data["temperature"] = temperature

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._base_url}/messages",
                    headers=headers,
                    json=data
                )

                if response.status_code != 200:
                    logger.error(f"[LLMService] MiniMax API error: {response.status_code} - {response.text}")
                    return self._mock_response(prompt, error=f"API error: {response.status_code}")

                result = response.json()

                # Extract content from MiniMax response
                content = ""
                if "content" in result:
                    for block in result["content"]:
                        if block.get("type") == "text":
                            content = block.get("text", "")
                            break

                return LLMResponse(
                    content=content,
                    model=result.get("model", self._model),
                    usage=result.get("usage", {}),
                    finish_reason=result.get("stop_reason", "stop"),
                    raw_response=result
                )

        except Exception as e:
            logger.error(f"[LLMService] MiniMax call failed: {e}", exc_info=True)
            return self._mock_response(prompt, error=str(e))

    async def _generate_langchain(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate using LangChain client"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            from langchain.schema import HumanMessage
            langchain_messages = [HumanMessage(content=m["content"]) for m in messages]

            llm_params = {}
            if temperature is not None:
                llm_params["temperature"] = temperature
            if max_tokens is not None:
                llm_params["max_tokens"] = max_tokens
            if stop_sequences:
                llm_params["stop"] = stop_sequences
            llm_params.update(kwargs)

            response = await self._client.ainvoke(messages, **llm_params)
            content = response.content if hasattr(response, 'content') else str(response)

            return LLMResponse(
                content=content,
                model=getattr(self._client, 'model', 'unknown'),
                usage={"prompt_tokens": len(prompt) // 2, "completion_tokens": len(content) // 2},
                finish_reason="stop",
                raw_response=response
            )

        except Exception as e:
            logger.error(f"[LLMService] LLM call failed: {e}", exc_info=True)
            return self._mock_response(prompt, error=str(e))

    def _mock_response(self, prompt: str, error: str = None) -> LLMResponse:
        """Generate mock response when no API key is configured"""
        mock_content = f"【系统提示】LLM API未配置或调用失败。\n\n收到您的请求: {prompt[:100]}...\n\n(正式集成后将返回AI生成的完整回答)"

        if error:
            mock_content += f"\n\n注意: 上次调用出错 - {error[:200]}"

        return LLMResponse(
            content=mock_content,
            model="mock",
            usage={"prompt_tokens": len(prompt) // 2, "completion_tokens": len(mock_content) // 2},
            finish_reason="stop"
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Chat completion interface"""
        if not self._initialized:
            user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            return self._mock_response(user_msg)

        if self._provider == "minimax":
            return await self._chat_minimax(messages, temperature, max_tokens)

        if self._client:
            return await self._chat_langchain(messages, temperature, max_tokens, **kwargs)

        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return self._mock_response(user_msg)

    async def _chat_minimax(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Chat using MiniMax Anthropic-compatible API"""
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Convert messages format for MiniMax
        minimax_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # System messages should come first in user role
                minimax_messages.append({"role": "user", "content": f"[System: {msg['content']}]"})
            else:
                minimax_messages.append({"role": msg["role"], "content": msg["content"]})

        data = {
            "model": self._model,
            "max_tokens": max_tokens or 4096,
            "messages": minimax_messages
        }

        if temperature is not None:
            data["temperature"] = temperature

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._base_url}/messages",
                    headers=headers,
                    json=data
                )

                if response.status_code != 200:
                    logger.error(f"[LLMService] MiniMax chat error: {response.status_code} - {response.text}")
                    user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
                    return self._mock_response(user_msg, error=f"API error: {response.status_code}")

                result = response.json()

                content = ""
                if "content" in result:
                    for block in result["content"]:
                        if block.get("type") == "text":
                            content = block.get("text", "")
                            break

                return LLMResponse(
                    content=content,
                    model=result.get("model", self._model),
                    usage=result.get("usage", {}),
                    finish_reason=result.get("stop_reason", "stop"),
                    raw_response=result
                )

        except Exception as e:
            logger.error(f"[LLMService] MiniMax chat failed: {e}", exc_info=True)
            user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            return self._mock_response(user_msg, error=str(e))

    async def _chat_langchain(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Chat using LangChain client"""
        try:
            from langchain.schema import HumanMessage, AIMessage, SystemMessage

            langchain_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))

            llm_params = {}
            if temperature is not None:
                llm_params["temperature"] = temperature
            if max_tokens is not None:
                llm_params["max_tokens"] = max_tokens
            llm_params.update(kwargs)

            response = await self._client.ainvoke(langchain_messages, **llm_params)
            content = response.content if hasattr(response, 'content') else str(response)

            return LLMResponse(
                content=content,
                model=getattr(self._client, 'model', 'unknown'),
                usage={"prompt_tokens": sum(len(m["content"]) for m in messages) // 2, "completion_tokens": len(content) // 2},
                finish_reason="stop",
                raw_response=response
            )

        except Exception as e:
            logger.error(f"[LLMService] Chat failed: {e}", exc_info=True)
            user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            return self._mock_response(user_msg, error=str(e))


# Global singleton instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
