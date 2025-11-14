"""
OpenRouter Model Auto-Updater
Automatically updates the best FREE models configuration

Schedule this to run weekly to always have the latest free models!
"""

import asyncio
import json
from pathlib import Path
from scripts.discover_openrouter_models import discover_free_models, test_model_availability


async def update_cost_optimization_config():
    """Update cost_optimization.yaml with latest free models"""

    print("🔄 Auto-updating OpenRouter free models...")
    print()

    # Discover models
    free_models = await discover_free_models()

    if not free_models:
        print("❌ Failed to discover models")
        return False

    # Test top models
    print("\n🧪 Testing top 10 models for availability...")
    working_models = []

    for model in free_models[:10]:
        print(f"   {model['name'][:50]:50s} ", end="")
        works = await test_model_availability(model['id'])
        if works:
            print("✅")
            working_models.append(model)
        else:
            print("❌")
        await asyncio.sleep(1)

    if not working_models:
        print("\n⚠️  No working models found, keeping existing config")
        return False

    # Pick best models by category
    best_models = {
        'code': None,
        'reasoning': None,
        'general': None
    }

    for model in working_models:
        name_lower = model['name'].lower()
        model_id_lower = model['id'].lower()

        # Code models
        if 'coder' in name_lower or 'code' in model_id_lower:
            if not best_models['code']:
                best_models['code'] = model

        # Reasoning models
        elif 'deepseek' in name_lower or 'r1' in model_id_lower:
            if not best_models['reasoning']:
                best_models['reasoning'] = model

        # General models
        elif 'gemini' in name_lower or 'flash' in name_lower:
            if not best_models['general']:
                best_models['general'] = model

    # Save recommendations
    recommendations = {
        'last_updated': str(asyncio.get_event_loop().time()),
        'working_models': [m['id'] for m in working_models],
        'recommended': {
            'code': best_models['code']['id'] if best_models['code'] else working_models[0]['id'],
            'reasoning': best_models['reasoning']['id'] if best_models['reasoning'] else working_models[0]['id'],
            'general': best_models['general']['id'] if best_models['general'] else working_models[0]['id']
        }
    }

    # Save to config
    config_file = Path(__file__).parent.parent / 'config' / 'openrouter_recommendations.json'
    with open(config_file, 'w') as f:
        json.dump(recommendations, f, indent=2)

    print(f"\n✅ Updated recommendations saved to {config_file}")
    print()
    print("📋 RECOMMENDED MODELS:")
    print(f"   Code:      {recommendations['recommended']['code']}")
    print(f"   Reasoning: {recommendations['recommended']['reasoning']}")
    print(f"   General:   {recommendations['recommended']['general']}")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(update_cost_optimization_config())
    exit(0 if success else 1)
