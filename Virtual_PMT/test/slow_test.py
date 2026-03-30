"""
Slower test to avoid rate limiting
"""

from tools.google_trends import GoogleTrendsTool
import time

tool = GoogleTrendsTool()

print("\n🐢 SLOW TEST MODE (avoids rate limiting)")
print("="*60)

tests = [
    ("pizza", "today 3-m", ""),           # Popular term, worldwide
    ("fitness", "today 3-m", "IN"),       # Popular term, India
]

for i, (keyword, timeframe, geo) in enumerate(tests, 1):
    print(f"\nTest {i}: '{keyword}' ({timeframe}, {geo or 'worldwide'})")
    
    try:
        result = tool.get_interest_over_time(keyword, timeframe, geo)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success!")
            print(f"   Interest: {result['current_interest']}/100")
            print(f"   Trend: {result['trend_direction']}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    if i < len(tests):
        print("⏳ Waiting 10 seconds before next test...")
        time.sleep(10)  # Wait 10 seconds between tests

print("\n" + "="*60)
print("✅ Slow test complete!")