"""Probe script for validating live Meta Model API credentials and tool calling loop."""
import sys
import time
import httpx
from claimlab.config import settings

def main():
    print("=" * 60)
    print(" CLAIMLAB - META MODEL API PROBE (T-META-01)")
    print("=" * 60)
    print(f"Target Model:    {settings.META_MODEL}")
    print(f"Target Endpoint: {settings.META_BASE_URL}/chat/completions")
    print(f"Current Mode:    {settings.MODEL_MODE}")
    
    masked_key = f"{settings.META_API_KEY[:4]}...{settings.META_API_KEY[-4:]}" if len(settings.META_API_KEY) > 8 else ("(EMPTY)" if not settings.META_API_KEY else "***")
    print(f"API Key:         {masked_key}")
    print("-" * 60)

    if not settings.META_API_KEY or settings.MODEL_MODE != "live":
        print("[!] Live Meta API key is not configured or MODEL_MODE is not 'live'.")
        print("To enable live mode, update your .env file:")
        print("    MODEL_MODE=live")
        print("    META_API_KEY=<your_actual_meta_api_key>")
        print("-" * 60)
        sys.exit(1)

    print("[*] Initiating live round-trip probe with function calling schema...")
    headers = {
        "Authorization": f"Bearer {settings.META_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.META_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful ClaimLab attention tutor. When asked to test calculations, call the run_experiment tool."},
            {"role": "user", "content": "Run an attention scaling experiment with dimension d_k=64 and 500 samples."}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "run_experiment",
                    "description": "Execute a verified numerical experiment recipe.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipe_id": {"type": "string", "enum": ["softmax_sensitivity_v1", "attention_scaling_v1", "causal_masking_v1"]},
                            "parameters": {"type": "object"}
                        },
                        "required": ["recipe_id", "parameters"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "max_tokens": 500
    }

    t0 = time.time()
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{settings.META_BASE_URL.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload
            )
            elapsed = time.time() - t0
            print(f"[*] Response received in {elapsed:.2f}s (HTTP {resp.status_code})")
            resp.raise_for_status()
            data = resp.json()
            
            choice = data["choices"][0]
            message = choice["message"]
            tool_calls = message.get("tool_calls", [])
            print("[+] Meta API probe SUCCEEDED!")
            print(f"    Finish reason: {choice.get('finish_reason')}")
            if tool_calls:
                print(f"    Tool call returned: {tool_calls[0]['function']['name']}")
                print(f"    Tool arguments:     {tool_calls[0]['function']['arguments']}")
            elif message.get("content"):
                print(f"    Model reply:        {message['content'][:150]}...")
            
            usage = data.get("usage", {})
            print(f"    Tokens used:        Prompt={usage.get('prompt_tokens', 0)}, Completion={usage.get('completion_tokens', 0)}")
            print("=" * 60)
            return 0
    except httpx.HTTPStatusError as e:
        print(f"[x] HTTP error from Meta API: {e.response.status_code} - {e.response.text}")
        sys.exit(2)
    except Exception as e:
        print(f"[x] Network or probe connection error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
