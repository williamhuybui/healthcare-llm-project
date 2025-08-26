# Agent Tool Usage Instructions

## Weather Queries
When user asks about weather, temperature, or current conditions:

1. **If no location specified:**
   - First use `get_city_by_ip()` to find user's location
   - Then use web search with query like "current weather in [City], [Region]"
   - Provide temperature, conditions, and relevant details

2. **If location is specified:**
   - Directly search for "current weather in [specified location]"

**Example workflow for "What's the temperature?":**
1. Call `get_city_by_ip()` → gets "San Francisco, California, US"
2. Search "current weather in San Francisco, California" 
3. Extract temperature and conditions from results

## Location-Based Queries
For questions about local information (restaurants, events, businesses):

1. Use `get_city_by_ip()` to determine user's location
2. Include that location in your web search query
3. Provide location-specific results

## Time-Sensitive Information
When current time context is needed:

1. Use `get_time()` to get current timestamp
2. Factor time into your recommendations (business hours, event timing, etc.)

## Mathematical Calculations
For any math problems, equations, or calculations:

1. Use `calculator(expression)` with the mathematical expression
2. Supports: +, -, *, /, **, sqrt(), sin(), cos(), tan(), log(), factorial(), pi, e
3. Handle factorial notation: "5!" becomes "factorial(5)"

## Tool Combination Examples

**"What restaurants are open near me right now?"**
1. `get_time()` → current time
2. `get_city_by_ip()` → user location  
3. Search "restaurants open now near [location]"

**"Is it raining where I am?"**
1. `get_city_by_ip()` → user location
2. Search "current weather rain [location]"

**"Calculate the tip for a $45 dinner"**
1. `calculator("45 * 0.18")` → standard 18% tip
2. `calculator("45 * 0.20")` → generous 20% tip