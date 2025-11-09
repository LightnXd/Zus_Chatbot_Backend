# Calculator Tool Integration - Test Cases & Documentation

## Overview
The calculator tool provides arithmetic operations through both a dedicated API endpoint and integrated chat functionality.

## API Endpoint: `/calculate`

### Method: GET

### Parameters:
- `expression` - Direct mathematical expression (URL-encoded)
- `text` - Natural language arithmetic question

### URL Encoding Note:
When using `+` in URLs, it must be URL-encoded as `%2B` to avoid being interpreted as a space.

## Test Cases

### ✅ Successful Calculations

#### 1. Direct Expression - Addition
```powershell
# Correct: Use %2B for plus sign
curl.exe "http://localhost:8000/calculate?expression=5%2B3"
# Expected: {"success":true,"expression":"5+3","result":8,"formatted":"5+3 = 8"}

# Alternative: Use quotes and escape
curl.exe "http://localhost:8000/calculate?expression=5+3" # May fail due to URL encoding
```

#### 2. Subtraction
```powershell
curl.exe "http://localhost:8000/calculate?expression=10-3"
# Expected: {"success":true,"expression":"10-3","result":7,"formatted":"10-3 = 7"}
```

#### 3. Multiplication
```powershell
curl.exe "http://localhost:8000/calculate?expression=6*7"
# Expected: {"success":true,"expression":"6*7","result":42,"formatted":"6*7 = 42"}
```

#### 4. Division
```powershell
curl.exe "http://localhost:8000/calculate?expression=100/4"
# Expected: {"success":true,"expression":"100/4","result":25,"formatted":"100/4 = 25"}
```

#### 5. Complex Expression with Parentheses
```powershell
curl.exe "http://localhost:8000/calculate?expression=(5%2B3)*2"
# Expected: {"success":true,"expression":"(5+3)*2","result":16,"formatted":"(5+3)*2 = 16"}
```

#### 6. Power/Exponentiation
```powershell
curl.exe "http://localhost:8000/calculate?expression=2**8"
# Expected: {"success":true,"expression":"2**8","result":256,"formatted":"2**8 = 256"}
```

#### 7. Modulo
```powershell
curl.exe "http://localhost:8000/calculate?expression=17%25"
# Note: % must be encoded as %25
# Expected: {"success":true,"expression":"17%5","result":2,"formatted":"17%5 = 2"}
```

#### 8. Natural Language - Addition
```powershell
curl.exe "http://localhost:8000/calculate?text=what+is+5+plus+3"
# Expected: {"success":true,"expression":"5 + 3","result":8,"formatted":"5 + 3 = 8"}
```

#### 9. Natural Language - Multiplication
```powershell
curl.exe "http://localhost:8000/calculate?text=calculate+10+times+2"
# Expected: {"success":true,"expression":"10 * 2","result":20,"formatted":"10 * 2 = 20"}
```

#### 10. Natural Language - Division
```powershell
curl.exe "http://localhost:8000/calculate?text=15+divided+by+3"
# Expected: {"success":true,"expression":"15 / 3","result":5,"formatted":"15 / 3 = 5"}
```

### ❌ Error Handling - Graceful Failures

#### 1. Division by Zero
```powershell
curl.exe "http://localhost:8000/calculate?expression=10/0"
# Expected: {"success":false,"error":"Division by zero is not allowed.","expression":"10/0"}
```

#### 2. Invalid Syntax
```powershell
curl.exe "http://localhost:8000/calculate?expression=5%2B%2B3"
# Expected: {"success":false,"error":"Invalid mathematical expression: ...","expression":"5++3"}
```

#### 3. Invalid Characters
```powershell
curl.exe "http://localhost:8000/calculate?expression=5%2Babc"
# Expected: {"success":false,"error":"Invalid expression. Only numbers and operators..."}
```

#### 4. No Expression Detected
```powershell
curl.exe "http://localhost:8000/calculate?text=hello"
# Expected: {"success":false,"error":"No arithmetic expression detected...","has_arithmetic_intent":false}
```

#### 5. Missing Parameters
```powershell
curl.exe "http://localhost:8000/calculate"
# Expected: Documentation response with examples
```

## Chat Integration Tests

### PowerShell Test Commands

#### 1. Simple Addition in Chat
```powershell
$body = @{question='what is 5 plus 3'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json'
```

**Expected Response:**
```json
{
  "response": "5 + 3 = 8",
  "planning_info": {
    "primary_action": "calculate",
    "calculation_performed": true,
    "calculation_result": {
      "success": true,
      "expression": "5 + 3",
      "result": 8,
      "formatted": "5 + 3 = 8"
    }
  }
}
```

#### 2. Complex Calculation in Chat
```powershell
$body = @{question='calculate (10 + 5) * 2'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json'
```

**Expected Response:**
```json
{
  "response": "(10 + 5) * 2 = 30",
  "planning_info": {
    "primary_action": "calculate",
    "calculation_performed": true,
    "calculation_result": {
      "success": true,
      "expression": "(10 + 5) * 2",
      "result": 30
    }
  }
}
```

#### 3. Division by Zero - Graceful Error
```powershell
$body = @{question='what is 10 divided by 0'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json'
```

**Expected Response:**
```json
{
  "response": "I cannot divide by zero. Division by zero is mathematically undefined...",
  "planning_info": {
    "primary_action": "calculate",
    "calculation_performed": true,
    "calculation_result": {
      "success": false,
      "error": "Division by zero is not allowed."
    }
  }
}
```

#### 4. Mixed Query - Calculation + Product Search
```powershell
$body = @{question='I need a tumbler for 5 + 3 people'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json'
```

**Expected Behavior:**
- Planner detects both calculation intent (5 + 3) and product search intent (tumbler)
- Calculator calculates: 5 + 3 = 8
- Product search finds tumblers
- LLM combines: "You need a tumbler for 8 people..."

## Agentic Planning Integration

### Decision Flow for Calculations

```
User Question: "what is 5 + 3"
    ↓
Entity Extraction:
  - Numbers detected: [5, 3]
  - Operator detected: [+]
  - Math expression: "5 + 3"
    ↓
Intent Analysis:
  - Calculation score: 0.9 (very high)
  - Product search score: 0.0
  - Outlet search score: 0.0
    ↓
Decision Making:
  - Action: CALCULATE
  - Confidence: 0.9
  - Reasoning: "Direct mathematical expression detected."
    ↓
Execution:
  - Extract expression: "5 + 3"
  - Calculate: eval("5 + 3") = 8
  - Format result: "5 + 3 = 8"
    ↓
Response:
  - Include calculation in system template
  - LLM generates natural response
  - Return calculation_result in planning_info
```

### Decision Logging Example

```json
{
  "decisions": [
    {
      "action": "calculate",
      "confidence": 0.9,
      "reasoning": "Calculation triggered (confidence: 0.90). Direct mathematical expression detected.",
      "detected_entities": {
        "has_math_expression": true,
        "has_numbers": true,
        "has_operators": true
      },
      "missing_info": [],
      "timestamp": "2025-11-09T16:30:00.000000"
    }
  ],
  "execution_plan": [
    "Extract mathematical expression from question",
    "Execute calculator tool",
    "Format calculation result"
  ]
}
```

## Supported Operations

| Operation | Symbol | Example | Result |
|-----------|--------|---------|--------|
| Addition | + | 5 + 3 | 8 |
| Subtraction | - | 10 - 3 | 7 |
| Multiplication | * | 6 * 7 | 42 |
| Division | / | 100 / 4 | 25 |
| Power | ** | 2 ** 8 | 256 |
| Modulo | % | 17 % 5 | 2 |
| Parentheses | () | (5 + 3) * 2 | 16 |

## Natural Language Patterns

| Pattern | Operator | Example |
|---------|----------|---------|
| "X plus Y" | + | "5 plus 3" → "5 + 3" |
| "X minus Y" | - | "10 minus 3" → "10 - 3" |
| "X times Y" | * | "6 times 7" → "6 * 7" |
| "X multiplied by Y" | * | "5 multiplied by 2" → "5 * 2" |
| "X divided by Y" | / | "100 divided by 4" → "100 / 4" |
| "what is X + Y" | Direct | "what is 5 + 3" → "5 + 3" |
| "calculate X * Y" | Direct | "calculate 10 * 2" → "10 * 2" |

## Error Messages

### Security Errors
```json
{
  "success": false,
  "error": "Invalid expression. Only numbers and operators (+, -, *, /, %, parentheses) are allowed.",
  "expression": "5+abc"
}
```

### Mathematical Errors
```json
{
  "success": false,
  "error": "Division by zero is not allowed.",
  "expression": "10/0"
}
```

### Syntax Errors
```json
{
  "success": false,
  "error": "Invalid mathematical expression: invalid syntax (<string>, line 1)",
  "expression": "5++"
}
```

### Detection Errors
```json
{
  "success": false,
  "error": "No arithmetic expression detected in the text.",
  "has_arithmetic_intent": false
}
```

## Integration Architecture

```
┌─────────────────────────────────────┐
│      User Question                  │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   Agentic Planner                   │
│   - Detect arithmetic intent        │
│   - Score: calculation vs others    │
│   - Decision: CALCULATE             │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   Calculator Tool                   │
│   1. Extract expression             │
│   2. Validate (security)            │
│   3. eval() execution               │
│   4. Error handling                 │
│   5. Format result                  │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   System Template Enhancement       │
│   CALCULATION RESULT:               │
│   5 + 3 = 8                        │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   LLM Response Generation           │
│   "The answer is 8."                │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   Response with Planning Info       │
│   {                                 │
│     response: "...",                │
│     planning_info: {                │
│       calculation_performed: true,  │
│       calculation_result: {...}     │
│     }                               │
│   }                                 │
└─────────────────────────────────────┘
```

## Complete Test Script

```powershell
# Test Script for Calculator Tool Integration

Write-Host "=== Calculator Tool Integration Tests ===" -ForegroundColor Cyan

# Test 1: Direct expression endpoint
Write-Host "`n1. Testing /calculate endpoint - Addition" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?expression=5%2B3"

# Test 2: Subtraction
Write-Host "`n2. Testing subtraction" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?expression=10-7"

# Test 3: Multiplication
Write-Host "`n3. Testing multiplication" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?expression=6*7"

# Test 4: Division
Write-Host "`n4. Testing division" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?expression=100/4"

# Test 5: Complex expression
Write-Host "`n5. Testing complex expression" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?expression=(5%2B3)*2"

# Test 6: Natural language
Write-Host "`n6. Testing natural language" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?text=what+is+15+plus+7"

# Test 7: Division by zero (error handling)
Write-Host "`n7. Testing division by zero" -ForegroundColor Yellow
curl.exe "http://localhost:8000/calculate?expression=10/0"

# Test 8: Chat integration - simple
Write-Host "`n8. Testing chat integration - simple" -ForegroundColor Yellow
$body = @{question='what is 5 plus 3'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json' | ConvertTo-Json -Depth 10

# Test 9: Chat integration - complex
Write-Host "`n9. Testing chat integration - complex" -ForegroundColor Yellow
$body = @{question='calculate (10 + 5) * 2 please'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json' | ConvertTo-Json -Depth 10

# Test 10: Chat integration - error handling
Write-Host "`n10. Testing chat integration - error" -ForegroundColor Yellow
$body = @{question='what is 100 divided by 0'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post -Body $body -ContentType 'application/json' | ConvertTo-Json -Depth 10

Write-Host "`n=== Tests Complete ===" -ForegroundColor Green
```

## Key Features Delivered

✅ **Calculator API Integration**
- `/calculate` endpoint with two modes (direct expression and natural language)
- Comprehensive error handling
- URL encoding support
- Security validation (only numbers and operators allowed)

✅ **Agentic Planning Integration**
- Automatic arithmetic intent detection
- Confidence-based decision making
- Decision logging with reasoning
- Expression extraction from natural language

✅ **Error Handling**
- Division by zero: Graceful error message
- Invalid syntax: Clear error response
- Invalid characters: Security validation
- No expression: Helpful feedback

✅ **Example Transcripts**
- Successful calculations: Multiple operation types
- Graceful failures: All error cases covered
- Natural language: Word-to-operator conversion
- Chat integration: Seamless calculator access

✅ **Tool Calling Objective Met**
- Detects arithmetic intent automatically
- Invokes calculator endpoint/function
- Parses responses correctly
- Handles errors without crashing
- Returns results in planning_info
