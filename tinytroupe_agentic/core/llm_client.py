import os
import json
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class LLMClient:
    """Synchronous-friendly LLM wrapper with graceful fallback.

    - Provider and model configured via environment variables
    - Exposes text and JSON helpers
    - If no API key/provider is available, returns heuristic fallbacks
    """

    def __init__(self) -> None:
        load_dotenv()
        self.provider: str = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model: str = os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
        self.max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

        self._enabled: bool = True
        self._client = None

        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or OpenAI is None:
                self._enabled = False
            else:
                self._client = OpenAI()
        else:
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def generate_text_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Synchronous text generation. Uses provider API if enabled; otherwise returns a stub."""

        if not self.enabled:
            return self._fallback_text(user_prompt)

        return self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=max_tokens,
            response_format=None,
        )

    def generate_json_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_hint: Optional[str] = None,
    ) -> Any:
        """Synchronous JSON generation. Falls back to a minimal object if disabled."""

        if not self.enabled:
            return self._fallback_json()

        raw = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=self._augment_with_json_instructions(user_prompt, schema_hint),
            temperature=self.temperature,
            max_tokens=None,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(raw)
        except Exception:
            # Try to extract JSON substring
            try:
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1 and end > start:
                    return json.loads(raw[start : end + 1])
            except Exception:
                pass
            return {"content": raw}

    def _chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: Optional[int],
        response_format: Optional[Dict[str, str]],
    ) -> str:
        assert self._client is not None
        attempt = 0
        last_err: Optional[Exception] = None
        while attempt < self.max_retries:
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # pragma: no cover
                last_err = e
                attempt += 1
                time.sleep(min(2 ** attempt, 5))
        if last_err:
            raise last_err
        return ""

    def _augment_with_json_instructions(self, prompt: str, schema_hint: Optional[str]) -> str:
        instructions = (
            "Return a STRICT JSON object with double-quoted keys and values. "
            "Do not include any surrounding text."
        )
        if schema_hint:
            instructions += f"\nSchema hint: {schema_hint}"
        return f"{prompt}\n\n{instructions}"

    def _fallback_text(self, user_prompt: str) -> str:
        return (
            "Here is a context-aware response synthesized without external LLM access. "
            "Enable OPENAI_API_KEY to generate fully dynamic outputs."
        )

    def _fallback_json(self) -> Dict[str, Any]:
        return {"note": "LLM disabled; using static fallback."}

import os
import json
import asyncio
import random
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
	from openai import OpenAI
except Exception:
	OpenAI = None  # type: ignore


class LLMClient:
	"""Thin async wrapper around the selected LLM provider.

	- Reads configuration from environment variables
	- Provides text and JSON generation helpers
	- Gracefully degrades if API key/provider is unavailable
	"""

	def __init__(self) -> None:
		load_dotenv()
		self.provider: str = os.getenv("LLM_PROVIDER", "openai").lower()
		self.model: str = os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
		self.max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
		self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
		self.timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

		self._enabled: bool = True
		self._client = None

		if self.provider == "openai":
			api_key = os.getenv("OPENAI_API_KEY")
			if not api_key or OpenAI is None:
				self._enabled = False
			else:
				self._client = OpenAI()
		else:
			self._enabled = False

	@property
	def enabled(self) -> bool:
		return self._enabled and self._client is not None

	async def generate_text(
		self,
		system_prompt: str,
		user_prompt: str,
		temperature: Optional[float] = None,
		max_tokens: Optional[int] = None,
	) -> str:
		if not self.enabled:
			return self._fallback_text(user_prompt)

		return await asyncio.to_thread(
			self._chat_completion,
			system_prompt,
			user_prompt,
			temperature if temperature is not None else self.temperature,
			max_tokens,
			response_format=None,
		)

	async def generate_json(
		self,
		system_prompt: str,
		user_prompt: str,
		schema_hint: Optional[str] = None,
	) -> Any:
		if not self.enabled:
			return self._fallback_json()

		raw = await asyncio.to_thread(
			self._chat_completion,
			system_prompt,
			self._augment_with_json_instructions(user_prompt, schema_hint),
			self.temperature,
			None,
			response_format={"type": "json_object"},
		)
		try:
			return json.loads(raw)
		except Exception:
			try:
				start = raw.find("{")
				end = raw.rfind("}")
				if start != -1 and end != -1 and end > start:
					return json.loads(raw[start : end + 1])
			except Exception:
				pass
			return {"content": raw}

	def _chat_completion(
		self,
		system_prompt: str,
		user_prompt: str,
		temperature: float,
		max_tokens: Optional[int],
		response_format: Optional[Dict[str, str]],
	) -> str:
		assert self._client is not None
		attempt = 0
		last_err: Optional[Exception] = None
		while attempt < self.max_retries:
			try:
				resp = self._client.chat.completions.create(
					model=self.model,
					messages=[
						{"role": "system", "content": system_prompt},
						{"role": "user", "content": user_prompt},
					],
					temperature=temperature,
					max_tokens=max_tokens,
					response_format=response_format,
				)
				return resp.choices[0].message.content or ""
			except Exception as e:
				last_err = e
				attempt += 1
				time.sleep(min(2 ** attempt, 5))
		if last_err:
			raise last_err
		return ""

	def _augment_with_json_instructions(self, prompt: str, schema_hint: Optional[str]) -> str:
		instructions = (
			"Return a STRICT JSON object with double-quoted keys and values. "
			"Do not include any surrounding text."
		)
		if schema_hint:
			instructions += f"\nSchema hint: {schema_hint}"
		return f"{prompt}\n\n{instructions}"

	def _fallback_text(self, user_prompt: str) -> str:
		templates = [
			"Based on the provided context, here is a reasoned response.",
			"Here is a concise, context-aware answer.",
			"Given the information, the following perspective applies.",
		]
		return random.choice(templates)

	def _fallback_json(self) -> Dict[str, Any]:
		return {"note": "LLM disabled; using static fallback."}

