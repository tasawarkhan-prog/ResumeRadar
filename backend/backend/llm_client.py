import os
import re
import json


class LLMClient:
    """Unified LLM client supporting Groq and Gemini.

    Priority for API keys:
      1. User-provided key (passed directly)
      2. Server .env key (GROQ_API_KEY / GEMINI_API_KEY)
    Provider is auto-detected from available keys if not specified.
    """

    def __init__(
        self,
        provider: str = None,
        groq_api_key: str = None,
        gemini_api_key: str = None,
    ):
        # Resolve keys: user-provided first, then env fallback
        self._groq_key = (groq_api_key or "").strip() or os.getenv("GROQ_API_KEY", "")
        self._gemini_key = (gemini_api_key or "").strip() or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")

        # Auto-detect provider from available keys
        if provider is None:
            if self._groq_key:
                provider = "groq"
            elif self._gemini_key:
                provider = "gemini"
            else:
                raise ValueError(
                    "No API key found. Provide a Groq or Gemini key in the UI, "
                    "or set GROQ_API_KEY / GEMINI_API_KEY in backend/.env"
                )

        self.provider = provider
        self._init_client()

    def _init_client(self):
        if self.provider == "groq":
            if not self._groq_key:
                raise ValueError("Groq selected but no GROQ_API_KEY found. Enter your key in the UI.")
            from groq import Groq
            self.client = Groq(api_key=self._groq_key)
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        elif self.provider == "gemini":
            if not self._gemini_key:
                raise ValueError("Gemini selected but no GEMINI_API_KEY found. Enter your key in the UI.")
            import google.generativeai as genai
            genai.configure(api_key=self._gemini_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.client = genai.GenerativeModel(model_name)

        else:
            raise ValueError(f"Unknown provider: '{self.provider}'. Use 'groq' or 'gemini'.")

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=4096,
            )
            return response.choices[0].message.content

        elif self.provider == "gemini":
            prompt = f"{system}\n\n{user}"
            response = self.client.generate_content(
                prompt,
                generation_config={"temperature": temperature, "max_output_tokens": 4096},
            )
            return response.text

    def complete_json(self, system: str, user: str) -> dict:
        json_system = system + "\n\nCRITICAL: Return ONLY valid JSON. No markdown fences, no explanation, no extra text."
        raw = self.complete(json_system, user, temperature=0.1).strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if m:
                raw = m.group(1).strip()

        # Remove control characters that break JSON parsing (literal \x00-\x1f except \t \n \r)
        raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)

        # Try parse — strict=False allows literal \n and \t inside strings
        try:
            return json.loads(raw, strict=False)
        except json.JSONDecodeError:
            # Try to extract the outermost JSON object
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    return json.loads(m.group(), strict=False)
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"LLM did not return valid JSON. Raw output snippet: {raw[:300]}")
