"""Quick test to verify Squad client works after API restart"""
import sys
sys.path.insert(0, ".")

from scripts.squad_client import Squad

print("Testing Squad Client...")
print("=" * 60)

squad = Squad()

print("\n1. Testing simple request...")
response = squad.ask("dev", "Create a simple hello world function in Python")

if response and len(response) > 10:
    print("✅ SUCCESS!")
    print(f"Response preview: {response[:200]}...")
else:
    print(f"❌ FAILED: {response}")

print("\n" + "=" * 60)
print("Test complete!")
