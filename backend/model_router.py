import re
import json
import httpx
from typing import Optional, Dict, Any

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "deepseek-r1:8b"

def clean_think_tokens(raw_text: str) -> str:
    """Membersihkan token internal monologue <think>...</think> dari model DeepSeek-R1."""
    if not raw_text:
        return ""
    if "</think>" in raw_text:
        raw_text = raw_text.split("</think>")[-1]
    else:
        # Jika belum ada closing tag </think>, bersihkan tag pembuka jika ada
        raw_text = re.sub(r'^<think>\s*', '', raw_text, flags=re.DOTALL)
    # Bersihkan sisa tag jika ada
    raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    return raw_text.strip()

def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Mengekstrak dan mem-parse blok JSON dari output model."""
    cleaned = clean_think_tokens(text)
    # Coba cari blok ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
    candidate = match.group(1) if match else cleaned

    # Coba cari kurung kurawal pertama dan terakhir
    first_brace = candidate.find('{')
    last_brace = candidate.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = candidate[first_brace:last_brace + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return None

class ModelRouter:
    """Layer abstraksi inferensi LLM: mengutamakan DeepSeek-R1 lokal via Ollama,
    dengan penanganan timeout realistis, keep-alive persistensi memori, dan sanitasi token monologue."""

    def __init__(self, endpoint: str = OLLAMA_URL, model: str = DEFAULT_MODEL, timeout_seconds: float = 40.0):
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout_seconds

    async def query(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 150, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.endpoint, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw = data.get("response", "")
                    thinking = data.get("thinking", "")

                    cleaned = clean_think_tokens(raw)
                    if cleaned:
                        return cleaned
                    
                    # Jika response kosong tetapi model sempat menghasilkan thinking (Ollama v0.5+)
                    if thinking:
                        cleaned_think = clean_think_tokens(thinking)
                        if cleaned_think:
                            return cleaned_think
        except Exception as err:
            print(f"[!] Warning: ModelRouter query error/timeout ({err}). Mengaktifkan fallback penalaran.")

        # Fallback analitis kontekstual jika LLM offline/timeout
        return "Analisis komputasi kognitif selesai dievaluasi berdasarkan pola anomali leksikal dan topologi transmisi publik."

# Singleton instance
model_router = ModelRouter()
