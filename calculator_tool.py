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
        
        # Attempt to parse expressions that may contain number words
        expr = self._words_to_expression(text)
        if expr:
            return expr

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

    def _words_to_expression(self, text: str) -> Optional[str]:
        """
        Convert a natural-language expression with number words into a numeric expression.
        Example: 'four plus 3 times six' -> '4 + 3 * 6'
        """
        if not text or not isinstance(text, str):
            return None

        # Normalize
        s = text.lower()
        s = s.replace('-', ' ')
        s = s.replace(',', ' ')

        # Map operator phrases to symbols
        op_patterns = {
            r'\bplus\b': '+',
            r'\badd\b': '+',
            r'\bminus\b': '-',
            r'\bsubtract\b': '-',
            r'\btimes\b': '*',
            r'\bx\b': '*',
            r'\bmultiplied by\b': '*',
            r'\bmultiply by\b': '*',
            r'\bdivided by\b': '/',
            r'\bdivide by\b': '/',
            r'\bover\b': '/',
            r'\bmodulo\b': '%',
            r'\bmod\b': '%',
            r'\bto the power of\b': '**',
            r'\bpower of\b': '**'
        }
        for pat, sym in op_patterns.items():
            s = re.sub(pat, f' {sym} ', s)

        tokens = s.split()

        # number word maps
        units = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
            'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
            'nineteen': 19
        }
        tens = {
            'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
            'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90
        }
        scales = {'hundred': 100, 'thousand': 1000, 'million': 1000000}

        def parse_number_words(seq):
            total = 0
            current = 0
            for word in seq:
                if word in units:
                    current += units[word]
                elif word in tens:
                    current += tens[word]
                elif word in scales:
                    if current == 0:
                        current = 1
                    current *= scales[word]
                    total += current
                    current = 0
                else:
                    # unknown token, can't parse
                    return None
            return total + current

        out_tokens = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            # if token is an operator symbol or parentheses
            if re.fullmatch(r'[\+\-\*\/\%\(\)\*\*]+', t):
                out_tokens.append(t)
                i += 1
                continue

            # if token is numeric already
            if re.fullmatch(r'\d+(?:\.\d+)?', t):
                out_tokens.append(t)
                i += 1
                continue

            # try to parse a run of number words
            j = i
            seq = []
            while j < len(tokens) and (tokens[j] in units or tokens[j] in tens or tokens[j] in scales):
                seq.append(tokens[j])
                j += 1

            if seq:
                val = parse_number_words(seq)
                if val is None:
                    # failed to parse; bail to next token
                    i += 1
                else:
                    out_tokens.append(str(val))
                    i = j
            else:
                # unknown token like words 'what', 'is', etc. skip
                i += 1

        if not out_tokens:
            return None

        expr = ' '.join(out_tokens)
        # Final validation: should contain at least one digit and one operator
        if re.search(r'\d', expr) and re.search(r'[\+\-\*\/\%]', expr):
            return expr
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
