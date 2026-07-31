from dataclasses import dataclass
from pathlib import Path

from agent.portkey import portkey_headers
from core.config import get_settings


EMERGENCY_TERMS = {
    "chest pain",
    "difficulty breathing",
    "cannot breathe",
    "suicidal",
    "kill myself",
    "overdose",
    "severe bleeding",
    "stroke symptoms",
}
PROMPT_INJECTION_TERMS = {"ignore previous instructions", "reveal system prompt", "bypass guardrails"}


@dataclass
class GuardrailResult:
    action: str
    message: str | None = None


class MedicalGuardrails:
    """Deterministic first line of defence, designed to complement NeMo Guardrails flows."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._nemo_rails = None

    def _get_nemo_rails(self):
        """Lazily initialize NeMo so local bootstrap does not require LLM credentials."""
        if not self.settings.nemo_guardrails_enabled:
            return None
        if self._nemo_rails is None:
            try:
                from nemoguardrails import LLMRails, RailsConfig

                config_path = Path(__file__).resolve().parent.parent / "rails"
                config = RailsConfig.from_path(str(config_path))
                if self.settings.portkey_api_key and self.settings.portkey_config_id:
                    config.models[0]["parameters"].update(
                        {
                            "api_key": self.settings.portkey_api_key,
                            "api_base": "https://api.portkey.ai/v1",
                            "default_headers": portkey_headers(self.settings),
                        }
                    )
                self._nemo_rails = LLMRails(config)
            except Exception:
                self._nemo_rails = False
        return self._nemo_rails or None

    async def validate_input(self, query: str) -> GuardrailResult:
        normalized = query.lower()
        if any(term in normalized for term in EMERGENCY_TERMS):
            return GuardrailResult(
                action="emergency",
                message=(
                    "This may be an emergency. Please contact local emergency services or go to the nearest "
                    "emergency department now. Do not wait for an online response."
                ),
            )
        if any(term in normalized for term in PROMPT_INJECTION_TERMS):
            return GuardrailResult(action="blocked", message="I can help with healthcare questions, but I cannot follow that request.")
        rails = self._get_nemo_rails()
        if rails:
            try:
                result = await rails.generate_async(messages=[{"role": "user", "content": query}])
                content = str(result.get("content", result)).strip().upper()
                if content.startswith("BLOCK"):
                    return GuardrailResult(action="blocked", message="I cannot help with that request.")
            except Exception:
                # The deterministic emergency and injection checks remain mandatory if NeMo is unavailable.
                pass
        return GuardrailResult(action="allow")

    def validate_output(self, answer: str) -> str:
        disclaimer = "\n\n*This is general health information, not a diagnosis or a substitute for a clinician.*"
        return answer if disclaimer.strip() in answer else answer.rstrip() + disclaimer
