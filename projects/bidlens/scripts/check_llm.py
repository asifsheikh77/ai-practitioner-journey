"""Quick connectivity/latency check for a model runtime (no RFP data sent).
python scripts/check_llm.py --provider gemini
Tiny prompt OK but real questions time out -> the model is slow (thinking/long prompt).
Tiny prompt also fails -> key, model name or network (VPN/proxy/firewall/region).
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bidlens.llm import LLMError, make_client


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=["ollama", "openai", "gemini"], default="ollama")
    p.add_argument("--model")
    a = p.parse_args()
    try:
        client = make_client(a.provider, a.model)
        t = time.perf_counter()
        out = client.complete("Reply with JSON only.", 'Return {"ok": true}', max_tokens=50)
        print(f"OK  {client.name}  {time.perf_counter() - t:.1f}s  -> {out.strip()[:80]}")
    except LLMError as e:
        print(f"FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
