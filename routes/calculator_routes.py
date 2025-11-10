"""
Calculator endpoint route handlers
"""
import logging
from calculator_tool import get_calculator

logger = logging.getLogger(__name__)

async def handle_calculate(expression: str = None, text: str = None):
    """
    Calculator API endpoint for arithmetic operations
    
    Supports two modes:
    1. Direct expression: /calculate?expression=5+3
    2. Natural language: /calculate?text=what is 5 plus 3
    """
    try:
        calculator = get_calculator()
        
        # Mode 1: Direct expression
        if expression:
            result = calculator.calculate(expression)
            return {
                "success": result["success"],
                "expression": result.get("expression"),
                "result": result.get("result"),
                "formatted": result.get("formatted"),
                "error": result.get("error"),
                "mode": "direct_expression"
            }
        
        # Mode 2: Natural language text
        elif text:
            result = calculator.parse_and_calculate(text)
            return {
                "success": result["success"],
                "expression": result.get("expression"),
                "result": result.get("result"),
                "formatted": result.get("formatted"),
                "error": result.get("error"),
                "original_text": result.get("original_text"),
                "mode": "natural_language"
            }
        
        # No input provided - return documentation
        else:
            return {
                "message": "Calculator API - Arithmetic Operations",
                "description": "Perform arithmetic calculations using direct expressions or natural language",
                "usage": {
                    "direct_expression": "/calculate?expression=<math_expression>",
                    "natural_language": "/calculate?text=<question>"
                },
                "supported_operations": {
                    "+": "Addition",
                    "-": "Subtraction",
                    "*": "Multiplication",
                    "/": "Division",
                    "**": "Power/Exponentiation",
                    "%": "Modulo/Remainder",
                    "()": "Parentheses for grouping"
                },
                "examples": {
                    "direct": [
                        {"expression": "5 + 3", "result": 8},
                        {"expression": "10 * 2", "result": 20},
                        {"expression": "(5 + 3) * 2", "result": 16},
                        {"expression": "100 / 4", "result": 25},
                        {"expression": "2 ** 8", "result": 256},
                        {"expression": "17 % 5", "result": 2}
                    ],
                    "natural_language": [
                        {"text": "what is 5 plus 3", "result": 8},
                        {"text": "calculate 10 times 2", "result": 20},
                        {"text": "15 divided by 3", "result": 5},
                        {"text": "what's 100 minus 25", "result": 75}
                    ]
                },
                "error_handling": {
                    "division_by_zero": "Returns error message",
                    "invalid_syntax": "Returns error message",
                    "invalid_characters": "Only numbers and operators allowed"
                }
            }
    
    except Exception as e:
        logger.error(f"Error in /calculate endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "mode": "error"
        }
