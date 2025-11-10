"""
Calculator Tool for Arithmetic Operations
Supports basic arithmetic with error handling and validation
"""

import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CalculatorTool:
    """
    Local calculator tool for arithmetic operations
    Supports: addition, subtraction, multiplication, division, power, modulo
    """
    
    def __init__(self):
        self.supported_operations = {
            '+': 'addition',
            '-': 'subtraction',
            '*': 'multiplication',
            '/': 'division',
            '**': 'power',
            '%': 'modulo'
        }
    
    def detect_arithmetic_intent(self, text: str) -> bool:
        """
        Detect if text contains arithmetic intent
        
        Returns:
            bool: True if arithmetic intent detected
        """
        arithmetic_keywords = [
            'calculate', 'compute', 'add', 'subtract', 'multiply', 'divide',
            'plus', 'minus', 'times', 'divided', 'sum', 'difference', 'product',
            'quotient', 'power', 'modulo', 'remainder', 'what is', 'how much'
        ]
        
        text_lower = text.lower()
        
        has_keyword = any(kw in text_lower for kw in arithmetic_keywords)
        has_numbers = bool(re.search(r'\d+', text))
        has_operators = any(op in text for op in ['+', '-', '*', '/', '=', 'x'])
        has_expression = bool(re.search(r'\d+\s*[\+\-\*\/\%]\s*\d+', text))
                
        return (has_keyword and has_numbers) or has_operators or has_expression
    
    def extract_expression(self, text: str) -> Optional[str]:
        """
        Extract mathematical expression from text
        
        Examples:
            "what is 5 + 3" -> "5 + 3"
            "calculate 10 * 2" -> "10 * 2"
            "15 - 7" -> "15 - 7"
        
        Returns:
            str: Extracted expression or None
        """
        # Pattern 1: Direct expression (numbers and operators)
        pattern1 = r'([\d\.\s\+\-\*\/\%\(\)]+)'
        matches = re.findall(pattern1, text)
        
        if matches:
            # Take the longest match that has both numbers and operators
            for match in sorted(matches, key=len, reverse=True):
                if re.search(r'\d', match) and re.search(r'[\+\-\*\/\%]', match):
                    return match.strip()
        
        word_to_op = {
            'plus': '+',
            'add': '+',
            'minus': '-',
            'subtract': '-',
            'times': '*',
            'multiply': '*',
            'multiplied by': '*',
            'divided by': '/',
            'divide': '/',
            'modulo': '%',
            'mod': '%',
            'power': '**',
            'to the power of': '**'
        }
        
        text_lower = text.lower()
        for word, op in word_to_op.items():
            if word in text_lower:
                pattern = rf'(\d+\.?\d*)\s*{word}\s*(\d+\.?\d*)'
                match = re.search(pattern, text_lower)
                if match:
                    return f"{match.group(1)} {op} {match.group(2)}"
        
        return None
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Calculate arithmetic expression
        
        Args:
            expression: Mathematical expression string
        
        Returns:
            Dict with result, success status, and optional error
        """        
        try:
            if not re.match(r'^[\d\.\s\+\-\*\/\%\(\)]+$', expression):
                return {
                    "success": False,
                    "error": "Invalid expression. Only numbers and operators (+, -, *, /, %, parentheses) are allowed.",
                    "expression": expression
                }
            
            result = eval(expression)
            
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 6)
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "formatted": f"{expression} = {result}"
            }
        
        except ZeroDivisionError:
            logger.error(f"❌ Division by zero: {expression}")
            return {
                "success": False,
                "error": "Division by zero is not allowed.",
                "expression": expression
            }
        
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in expression: {expression}")
            return {
                "success": False,
                "error": f"Invalid mathematical expression: {str(e)}",
                "expression": expression
            }
        
        except Exception as e:
            logger.error(f"❌ Calculation error: {expression} - {str(e)}")
            return {
                "success": False,
                "error": f"Calculation error: {str(e)}",
                "expression": expression
            }
    
    def parse_and_calculate(self, text: str) -> Dict[str, Any]:
        """
        Detect, extract, and calculate from natural language text
        
        Args:
            text: Natural language text
        
        Returns:
            Dict with calculation result or error
        """
        # Check if text contains arithmetic intent
        if not self.detect_arithmetic_intent(text):
            return {
                "success": False,
                "error": "No arithmetic expression detected in the text.",
                "has_arithmetic_intent": False
            }
        
        # Extract expression
        expression = self.extract_expression(text)
        
        if not expression:
            return {
                "success": False,
                "error": "Could not extract a valid mathematical expression.",
            "has_arithmetic_intent": True
        }
        
        result = self.calculate(expression)
        result["original_text"] = text
        return result


_calculator = None


def get_calculator() -> CalculatorTool:
    """Get or create global calculator instance"""
    global _calculator
    if _calculator is None:
        _calculator = CalculatorTool()
    return _calculator
