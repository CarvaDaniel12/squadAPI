"""
OpenRouter Models Discovery
Automatically finds FREE models available on OpenRouter

Uses OpenRouter's models API to discover which models are currently free.
Run this periodically to update your free models list!
"""

import asyncio
import aiohttp
import os
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv(Path(__file__).parent.parent / '.env')


async def discover_free_models():
    """Fetch all available models from OpenRouter and filter free ones"""

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env")
        return []

    print("🔍 Discovering FREE models on OpenRouter...")
    print("="*70)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers
            ) as resp:
                if resp.status != 200:
                    print(f"❌ API request failed: {resp.status}")
                    return []

                data = await resp.json()
                models = data.get('data', [])

        # Filter for free models
        free_models = []
        for model in models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '0'))
            completion_price = float(pricing.get('completion', '0'))

            # Check if both input and output are free
            if prompt_price == 0 and completion_price == 0:
                free_models.append({
                    'id': model['id'],
                    'name': model.get('name', model['id']),
                    'context': model.get('context_length', 0),
                    'description': model.get('description', '')[:100]
                })

        # Sort by context length (bigger = better usually)
        free_models.sort(key=lambda x: x['context'], reverse=True)

        print(f"\n✅ Found {len(free_models)} FREE models!\n")

        # Categorize by size/capability
        print("🌟 TOP FREE MODELS (by context length):\n")

        for i, model in enumerate(free_models[:15], 1):  # Top 15
            context_k = model['context'] // 1000
            print(f"{i:2d}. {model['name']}")
            print(f"    ID: {model['id']}")
            print(f"    Context: {context_k}K tokens")
            if model['description']:
                print(f"    {model['description']}")
            print()

        # Generate Python code for best models
        print("\n" + "="*70)
        print("📝 COPY THIS TO YOUR SCRIPT:")
        print("="*70 + "\n")

        print("OPENROUTER_FREE_MODELS = [")
        for model in free_models[:5]:  # Top 5 for the script
            print(f"    {{")
            print(f"        'name': '{model['name']}',")
            print(f"        'id': '{model['id']}',")
            print(f"        'description': '{model['description'][:80]}...',")
            print(f"        'context': {model['context']}")
            print(f"    }},")
        print("]")

        # Save to file
        output_file = Path(__file__).parent.parent / 'config' / 'openrouter_free_models.json'
        with open(output_file, 'w') as f:
            json.dump(free_models, f, indent=2)

        print(f"\n💾 Saved full list to: {output_file}")

        return free_models

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_model_availability(model_id: str):
    """Quick test if a model actually works"""

    api_key = os.getenv('OPENROUTER_API_KEY')

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://squad-api.local",
        "X-Title": "Squad API"
    }

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 5
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                return resp.status == 200
    except:
        return False


async def main():
    """Run discovery and optionally test top models"""

    print("="*70)
    print("🔍 OPENROUTER FREE MODELS DISCOVERY")
    print("="*70 + "\n")

    free_models = await discover_free_models()

    if not free_models:
        print("\n❌ No free models found or API error")
        return 1

    # Ask if user wants to test models
    print("\n" + "="*70)
    print("🧪 Testing availability of top 5 models...")
    print("="*70 + "\n")

    working_models = []

    for model in free_models[:5]:
        print(f"Testing {model['name']}...", end=" ")
        works = await test_model_availability(model['id'])
        if works:
            print("✅ WORKS")
            working_models.append(model)
        else:
            print("❌ Unavailable (might be temporarily down)")
        await asyncio.sleep(1)  # Rate limit

    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total free models: {len(free_models)}")
    print(f"Tested: 5")
    print(f"Working: {len(working_models)}")
    print()

    if working_models:
        print("✅ RECOMMENDED MODELS (tested and working):")
        for model in working_models:
            print(f"   • {model['id']}")

    print()
    print("💡 TIP: Run this script weekly to discover new free models!")
    print("   OpenRouter rotates their free tier offerings regularly.")
    print()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
