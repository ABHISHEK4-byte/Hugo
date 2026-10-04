from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from app.config import ANTHROPIC_API_KEY, DEFAULT_MODEL, GEMINI_API_KEY, OPENAI_API_KEY


class LLMClient:
    def __init__(self, provider: str, model: str | None = None) -> None:
        self.provider = provider.lower()
        self.model = model or self._default_model()

    def _default_model(self) -> str:
        if self.provider == "openai":
            return DEFAULT_MODEL
        if self.provider == "anthropic":
            return "claude-3-haiku-20240307"
        if self.provider == "gemini":
            return "gemini-1.5-flash"
        return "local"

    def generate(self, prompt: str, system_prompt: str = "You are a helpful Hugo agent.") -> str:
        if self.provider == "openai":
            return self._call_openai(prompt, system_prompt)
        if self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        if self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt)
        return f"[local fallback] {prompt}"

    def _call_openai(self, prompt: str, system_prompt: str) -> str:
        if not OPENAI_API_KEY:
            return "OpenAI API key is not configured. Using local fallback."

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content or "No response generated."

    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        if not ANTHROPIC_API_KEY:
            return "Anthropic API key is not configured. Using local fallback."

        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=self.model,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        if not GEMINI_API_KEY:
            return "Gemini API key is not configured. Using local fallback."

        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(f"{system_prompt}\n\n{prompt}")
        return response.text
