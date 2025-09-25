"""Test Tools for LangGraph Agents

A collection of tools for testing and demonstrating agent capabilities:
- Calculator for mathematical expressions
- Time retrieval
- Public IP address lookup
- City location by IP
- Web search via Tavily
"""

import math
import re
import time
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Evaluates mathematical expressions safely.
    
    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, factorial, pi, e
    Examples: 2+2, sqrt(16), 5!, sin(pi/2)
    """
    try:
        # Safe evaluation namespace
        safe_dict = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "pi": math.pi, "e": math.e, "factorial": math.factorial
        }
        
        # Handle factorial notation (5! -> factorial(5))
        if '!' in expression and 'factorial(' not in expression:
            expression = re.sub(r'(\d+)!', r'factorial(\1)', expression)
        
        result = eval(expression, safe_dict)
        return f"Result: {result}"
    
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_time() -> str:
    """Returns the current date and time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


@tool
def get_public_ip(_: str = "") -> str:
    """Returns the public IP address using an external service."""
    try:
        import requests
        ip = requests.get('https://api.ipify.org', timeout=5).text
        return f"Public IP: {ip}"
    except Exception as e:
        return f"Error: {str(e)}"
    

@tool
def get_city_by_ip(ip: str = "") -> str:
    """Returns the city for a given IP address.
    
    If no IP is provided, uses the current public IP.
    """
    try:
        import requests
        if not ip:
            ip = requests.get('https://api.ipify.org', timeout=5).text
        
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        data = response.json()
        city = data.get('city', 'Unknown')
        country = data.get('country', 'Unknown')
        
        return f"Location for IP {ip}: {city}, {country}"
    except Exception as e:
        return f"Error: {str(e)}"


def get_all_tools():
    """Returns a list of all available tools."""
    return [calculator, get_time, get_public_ip, get_city_by_ip]


if __name__ == '__main__':
    import requests
    ip = requests.get('https://api.ipify.org', timeout=5).text
    res = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
    city = res.json().get('city', 'Unknown')
    print(ip, city)