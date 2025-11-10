"""
Agentic Planning System for ZUS Chatbot
Implements explicit planner/controller loop with decision logging and missing info detection
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Available action types"""
    SEARCH_PRODUCTS = "search_products"
    SEARCH_OUTLETS = "search_outlets"
    CALCULATE = "calculate"
    ASK_CLARIFICATION = "ask_clarification"
    CONVERSATIONAL = "conversational"
    HYBRID_SEARCH = "hybrid_search"


class InformationGap(Enum):
    """Types of missing information"""
    MISSING_LOCATION = "missing_location"
    MISSING_PRODUCT_TYPE = "missing_product_type"
    MISSING_PRICE_RANGE = "missing_price_range"
    MISSING_CAPACITY = "missing_capacity"
    MISSING_CALCULATION_EXPRESSION = "missing_calculation_expression"
    AMBIGUOUS_INTENT = "ambiguous_intent"
    INCOMPLETE_CONTEXT = "incomplete_context"


@dataclass
class Decision:
    """Represents a single decision in the planning process"""
    action: ActionType
    confidence: float  # 0.0 to 1.0
    reasoning: str
    detected_entities: Dict[str, Any] = field(default_factory=dict)
    missing_info: List[InformationGap] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "detected_entities": self.detected_entities,
            "missing_info": [gap.value for gap in self.missing_info],
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PlannerOutput:
    """Output from the planner containing actions and analysis"""
    primary_action: ActionType = ActionType.CONVERSATIONAL
    secondary_actions: List[ActionType] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    should_ask_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)
    execution_plan: List[str] = field(default_factory=list)
    
    def get_decision_log(self) -> List[Dict]:
        """Get all decisions as dictionaries"""
        return [d.to_dict() for d in self.decisions]


class AgenticPlanner:
    """
    Explicit planner/controller for the chatbot
    
    Responsibilities:
    1. Intent analysis and entity extraction
    2. Missing information detection
    3. Action planning with decision logging
    4. Follow-up question generation
    5. Execution ordering
    """
    
    def __init__(self):
        self.product_keywords = {
            'tumbler', 'cup', 'drinkware', 'bottle', 'price', 'cost',
            'product', 'item', 'capacity', 'size', 'design', 'color', 'material',
            'recommend', 'suggest', 'best', 'water', 'coffee', 'drink', 'hot', 'cold',
            'all day', 'frozee', 'buddy', 'zus', 'merchandise', 'gift', 'set',
            'list', 'show', 'display', 'top', 'popular', 'available',
            'cheap', 'cheapest', 'affordable', 'budget', 'expensive', 'inexpensive'
        }
        
        self.outlet_keywords = {
            'outlet', 'location', 'store', 'shop', 'address', 'where', 'near',
            'nearest', 'branch', 'city', 'area', 'zone', 'kuala lumpur', 'selangor',
            'mall', 'visit', 'open', 'hours', 'available', 'find', 'buy', 'purchase',
            'map', 'google maps', 'directions'
        }
        
        self.calculation_keywords = {
            'calculate', 'compute', 'add', 'subtract', 'multiply', 'divide',
            'plus', 'minus', 'times', 'divided', 'sum', 'difference', 'product',
            'quotient', 'power', 'modulo', 'remainder', 'what is', 'how much',
            'math', 'arithmetic'
        }
        
        self.price_indicators = {'cheap', 'affordable', 'expensive', 'budget', 'rm', 'ringgit', 'price'}
        self.capacity_indicators = {'large', 'small', 'big', 'ml', 'liter', 'capacity', 'size'}
        self.location_cities = {
            'shah alam', 'petaling jaya', 'subang', 'klang', 'kuala lumpur',
            'kl', 'pj', 'ampang', 'cheras', 'kepong', 'bangsar', 'damansara'
        }
    
    def plan(self, question: str, conversation_context: Dict = None) -> PlannerOutput:
        """
        Main planning method - implements the planner/controller loop
        
        Args:
            question: User's question
            conversation_context: Previous conversation context and metadata
            
        Returns:
            PlannerOutput with actions, decisions, and clarification questions
        """
        
        question_lower = question.lower()
        output = PlannerOutput()
        
        # Step 1: Extract entities and detect intent
        entities = self._extract_entities(question_lower, conversation_context)
        
        # Step 2: Detect missing information
        missing_info = self._detect_missing_info(question_lower, entities, conversation_context)
        
        # Step 3: Analyze intent and confidence
        intent_scores = self._analyze_intent(question_lower, entities)
        
        # Step 4: Make decisions with reasoning
        decisions = self._make_decisions(question_lower, entities, intent_scores, missing_info)
        output.decisions = decisions

        # Step 5: Determine primary action
        primary_decision = max(decisions, key=lambda d: d.confidence)
        output.primary_action = primary_decision.action
        
        # Step 6: Determine secondary actions
        output.secondary_actions = [
            d.action for d in decisions 
            if d.action != output.primary_action and d.confidence > 0.3
        ]
        
        # Step 7: Generate clarification questions if needed
        if missing_info and self._should_ask_clarification(missing_info, primary_decision):
            output.should_ask_clarification = True
            output.clarification_questions = self._generate_clarification_questions(
                missing_info, entities, primary_decision
            )

        # Step 8: Create execution plan
        output.execution_plan = self._create_execution_plan(output)
        return output
    
    def _extract_entities(self, question: str, context: Dict = None) -> Dict[str, Any]:
        """Extract entities from question and context"""
        entities = {
            'product_mentions': [],
            'location_mentions': [],
            'price_range': None,
            'capacity_mentions': [],
            'product_keywords': [],
            'outlet_keywords': [],
            'has_context_reference': False
        }
        
        # Check for context references (that, it, there, etc.)
        context_refs = ['that', 'it', 'there', 'them', 'those', 'this', 'these']
        if any(ref in question for ref in context_refs):
            entities['has_context_reference'] = True
        
        # Extract product keywords
        for keyword in self.product_keywords:
            if keyword in question:
                entities['product_keywords'].append(keyword)
        
        # Extract outlet keywords
        for keyword in self.outlet_keywords:
            if keyword in question:
                entities['outlet_keywords'].append(keyword)
        
        # Extract locations
        for city in self.location_cities:
            if city in question:
                entities['location_mentions'].append(city)
        
        # Extract price indicators
        if any(indicator in question for indicator in self.price_indicators):
            # Try to extract price range
            import re
            price_match = re.search(r'rm\s*(\d+)', question)
            if price_match:
                entities['price_range'] = int(price_match.group(1))
        
        # Extract capacity mentions
        for indicator in self.capacity_indicators:
            if indicator in question:
                entities['capacity_mentions'].append(indicator)
        
        # Use conversation context metadata if available
        if context:
            metadata = context.get('metadata', {})
            # mentioned_products is a boolean, not a list - just check if true
            if metadata.get('mentioned_products') and isinstance(metadata.get('mentioned_products'), bool):
                # Don't extend, just note that products were mentioned
                pass
            # mentioned_cities is actually a list, so we can extend
            if metadata.get('mentioned_cities') and isinstance(metadata.get('mentioned_cities'), list):
                entities['location_mentions'].extend(metadata['mentioned_cities'])
        
        return entities
    
    def _detect_missing_info(
        self, 
        question: str, 
        entities: Dict, 
        context: Dict = None
    ) -> List[InformationGap]:
        """Detect what information is missing for complete execution"""
        missing = []
        
        # Check for /calculate command without expression
        import re
        is_calculate_command = question.strip().startswith('/calculate')
        has_math_expression = bool(re.search(r'\d+\s*[\+\-\*\/\%]\s*\d+', question))
        
        if is_calculate_command and not has_math_expression:
            # /calculate was called but no expression provided
            missing.append(InformationGap.MISSING_CALCULATION_EXPRESSION)
        
        # Check if intent is ambiguous
        has_product_keywords = len(entities['product_keywords']) > 0
        has_outlet_keywords = len(entities['outlet_keywords']) > 0
        
        if not has_product_keywords and not has_outlet_keywords:
            # Purely conversational or ambiguous
            if entities['has_context_reference'] and not context:
                missing.append(InformationGap.INCOMPLETE_CONTEXT)
            elif len(question.split()) < 4:  # Very short question
                missing.append(InformationGap.AMBIGUOUS_INTENT)
        
        # Check for missing location in outlet queries
        if has_outlet_keywords:
            location_query_indicators = ['where', 'find', 'location', 'near', 'in']
            if any(ind in question for ind in location_query_indicators):
                if not entities['location_mentions']:
                    # Check if it's a count query (doesn't need location)
                    if 'how many' not in question and 'count' not in question:
                        missing.append(InformationGap.MISSING_LOCATION)
        
        # Check for missing product type in product queries
        if has_product_keywords:
            if 'recommend' in question or 'suggest' in question or 'best' in question:
                if not entities['product_mentions'] and not entities['capacity_mentions']:
                    missing.append(InformationGap.MISSING_PRODUCT_TYPE)
        
        # Note: Removed MISSING_PRICE_RANGE check - price filtering can be done during product search
        # The LLM can sort by price without needing explicit price range clarification
        
        # Check for missing capacity
        if 'large' in question or 'big' in question or 'small' in question:
            if not any(c in question for c in ['ml', 'liter', 'oz']):
                missing.append(InformationGap.MISSING_CAPACITY)
        
        return missing
    
    def _analyze_intent(self, question: str, entities: Dict) -> Dict[str, float]:
        """Analyze intent and return confidence scores"""
        scores = {
            'product_search': 0.0,
            'outlet_search': 0.0,
            'calculation': 0.0,
            'conversational': 0.0,
            'hybrid': 0.0
        }
        
        # Calculation scoring (check first - highest priority for math)
        import re
        has_calculation_keyword = any(kw in question for kw in self.calculation_keywords)
        has_math_operators = bool(re.search(r'[\+\-\*\/\%\=]', question))
        has_numbers = bool(re.search(r'\d+', question))
        has_math_expression = bool(re.search(r'\d+\s*[\+\-\*\/\%]\s*\d+', question))
        
        # Check if it's a slash command /calculate
        is_calculate_command = question.strip().startswith('/calculate')
        
        # Product/outlet intent should override calculation if present
        has_clear_product_intent = len(entities['product_keywords']) >= 2 or 'list' in question or 'show' in question
        has_clear_outlet_intent = len(entities['outlet_keywords']) >= 2
        
        calc_score = 0.0
        if has_math_expression:
            calc_score = 0.9  # Very high confidence for clear expressions
        elif is_calculate_command:
            # /calculate command without expression - still mark as calculation
            if has_math_expression or (has_math_operators and has_numbers):
                calc_score = 0.9
            else:
                # /calculate but no expression - lower confidence, need clarification
                calc_score = 0.7
        elif has_calculation_keyword and has_numbers and has_math_operators and not has_clear_product_intent:
            # Only trigger if has BOTH numbers AND operators AND no clear product intent
            calc_score = 0.7
        elif has_math_operators and has_numbers and not has_clear_product_intent:
            calc_score = 0.6
        scores['calculation'] = calc_score
        
        # Product search scoring
        product_score = len(entities['product_keywords']) * 0.2
        if entities['price_range']:
            product_score += 0.15
        if entities['capacity_mentions']:
            product_score += 0.15
        scores['product_search'] = min(product_score, 1.0)
        
        # Outlet search scoring
        outlet_score = len(entities['outlet_keywords']) * 0.2
        if entities['location_mentions']:
            outlet_score += 0.3
        if 'map' in question or 'directions' in question:
            outlet_score += 0.2
        scores['outlet_search'] = min(outlet_score, 1.0)
        
        # Hybrid search (both products and outlets)
        if scores['product_search'] > 0.3 and scores['outlet_search'] > 0.3:
            scores['hybrid'] = (scores['product_search'] + scores['outlet_search']) / 2
        
        # Conversational scoring
        greetings = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'okay', 'ok']
        if any(g in question for g in greetings):
            scores['conversational'] = 0.8
        elif scores['product_search'] < 0.3 and scores['outlet_search'] < 0.3 and scores['calculation'] < 0.3:
            scores['conversational'] = 0.6
        
        return scores
    
    def _make_decisions(
        self, 
        question: str, 
        entities: Dict, 
        intent_scores: Dict,
        missing_info: List[InformationGap]
    ) -> List[Decision]:
        """Make decisions with explicit reasoning"""
        decisions = []
        
        # Decision 0: Should we calculate? (Check first - highest priority)
        if intent_scores['calculation'] > 0.5:
            reasoning = f"Calculation triggered (confidence: {intent_scores['calculation']:.2f}). "
            
            import re
            if re.search(r'\d+\s*[\+\-\*\/\%]\s*\d+', question):
                reasoning += "Direct mathematical expression detected. "
            else:
                reasoning += "Arithmetic intent detected with numbers. "
            
            decisions.append(Decision(
                action=ActionType.CALCULATE,
                confidence=intent_scores['calculation'],
                reasoning=reasoning,
                detected_entities=entities,
                missing_info=[]
            ))
        
        # Decision 1: Should we search products?
        if intent_scores['product_search'] > 0.3:
            reasoning = f"Product search triggered (confidence: {intent_scores['product_search']:.2f}). "
            reasoning += f"Detected {len(entities['product_keywords'])} product keywords: {entities['product_keywords'][:3]}. "
            
            if entities['price_range']:
                reasoning += f"Price range specified: RM{entities['price_range']}. "
            if entities['capacity_mentions']:
                reasoning += f"Capacity indicators found: {entities['capacity_mentions']}. "
            
            decisions.append(Decision(
                action=ActionType.SEARCH_PRODUCTS,
                confidence=intent_scores['product_search'],
                reasoning=reasoning,
                detected_entities=entities,
                missing_info=[gap for gap in missing_info if gap in [
                    InformationGap.MISSING_PRODUCT_TYPE,
                    InformationGap.MISSING_PRICE_RANGE,
                    InformationGap.MISSING_CAPACITY
                ]]
            ))
        
        # Decision 2: Should we search outlets?
        if intent_scores['outlet_search'] > 0.3:
            reasoning = f"Outlet search triggered (confidence: {intent_scores['outlet_search']:.2f}). "
            reasoning += f"Detected {len(entities['outlet_keywords'])} outlet keywords: {entities['outlet_keywords'][:3]}. "
            
            if entities['location_mentions']:
                reasoning += f"Location specified: {entities['location_mentions']}. "
            if 'map' in question or 'directions' in question:
                reasoning += "Maps URL requested. "
            
            decisions.append(Decision(
                action=ActionType.SEARCH_OUTLETS,
                confidence=intent_scores['outlet_search'],
                reasoning=reasoning,
                detected_entities=entities,
                missing_info=[gap for gap in missing_info if gap == InformationGap.MISSING_LOCATION]
            ))
        
        # Decision 3: Hybrid search
        if intent_scores['hybrid'] > 0.4:
            reasoning = f"Hybrid search triggered (confidence: {intent_scores['hybrid']:.2f}). "
            reasoning += f"Question requires both product and outlet information. "
            
            decisions.append(Decision(
                action=ActionType.HYBRID_SEARCH,
                confidence=intent_scores['hybrid'],
                reasoning=reasoning,
                detected_entities=entities,
                missing_info=missing_info
            ))
        
        # Decision 4: Should we ask for clarification?
        if missing_info and len(missing_info) >= 2:
            reasoning = f"Clarification needed due to {len(missing_info)} missing pieces of information: "
            reasoning += ", ".join([gap.value for gap in missing_info]) + ". "
            
            decisions.append(Decision(
                action=ActionType.ASK_CLARIFICATION,
                confidence=0.7,
                reasoning=reasoning,
                detected_entities=entities,
                missing_info=missing_info
            ))
        
        # Decision 5: Conversational mode
        if intent_scores['conversational'] > 0.5:
            reasoning = f"Conversational mode triggered (confidence: {intent_scores['conversational']:.2f}). "
            
            if entities['has_context_reference']:
                reasoning += "Question references previous context. "
            
            decisions.append(Decision(
                action=ActionType.CONVERSATIONAL,
                confidence=intent_scores['conversational'],
                reasoning=reasoning,
                detected_entities=entities,
                missing_info=missing_info
            ))
        
        # If no clear decisions, default to conversational
        if not decisions:
            decisions.append(Decision(
                action=ActionType.CONVERSATIONAL,
                confidence=0.5,
                reasoning="No clear product, outlet, or calculation intent detected. Defaulting to conversational mode.",
                detected_entities=entities,
                missing_info=missing_info
            ))
        
        return decisions
    
    def _should_ask_clarification(
        self, 
        missing_info: List[InformationGap], 
        primary_decision: Decision
    ) -> bool:
        """Determine if we should ask clarification before proceeding"""
        # Don't ask for clarification in conversational mode
        if primary_decision.action == ActionType.CONVERSATIONAL:
            return False
        
        # Always ask for clarification if calculation expression is missing
        if InformationGap.MISSING_CALCULATION_EXPRESSION in missing_info:
            return True
        
        # Ask if we have critical missing information
        critical_gaps = [
            InformationGap.AMBIGUOUS_INTENT,
            InformationGap.INCOMPLETE_CONTEXT
        ]
        
        if any(gap in missing_info for gap in critical_gaps):
            return True
        
        # Ask if we have multiple missing pieces and low confidence
        if len(missing_info) >= 2 and primary_decision.confidence < 0.6:
            return True
        
        return False
    
    def _generate_clarification_questions(
        self, 
        missing_info: List[InformationGap],
        entities: Dict,
        primary_decision: Decision
    ) -> List[str]:
        """Generate specific follow-up questions based on missing information"""
        questions = []
        
        for gap in missing_info:
            if gap == InformationGap.MISSING_CALCULATION_EXPRESSION:
                questions.append(
                    "What would you like me to calculate? Please provide a mathematical expression (e.g., 5 + 3, 10 * 8)."
                )
            
            elif gap == InformationGap.MISSING_LOCATION:
                questions.append(
                    "Which area are you looking for? For example: Shah Alam, Petaling Jaya, Subang, or Kuala Lumpur?"
                )
            
            elif gap == InformationGap.MISSING_PRODUCT_TYPE:
                questions.append(
                    "What type of drinkware are you interested in? We have tumblers, water bottles, cups, and gift sets."
                )
            
            elif gap == InformationGap.MISSING_PRICE_RANGE:
                questions.append(
                    "What's your budget? Our products range from RM20 to RM200."
                )
            
            elif gap == InformationGap.MISSING_CAPACITY:
                questions.append(
                    "What capacity are you looking for? We have options from 300ml to 1000ml."
                )
            
            elif gap == InformationGap.AMBIGUOUS_INTENT:
                questions.append(
                    "Would you like to know about our products or outlet locations?"
                )
            
            elif gap == InformationGap.INCOMPLETE_CONTEXT:
                questions.append(
                    "Could you provide more details about what you're looking for?"
                )
        
        return questions
    
    def _create_execution_plan(self, output: PlannerOutput) -> List[str]:
        """Create step-by-step execution plan"""
        plan = []
        
        if output.should_ask_clarification:
            plan.append("Ask user for clarification on missing information")
            plan.append("Wait for user response before proceeding")
        else:
            if output.primary_action == ActionType.CALCULATE:
                plan.append("Extract mathematical expression from question")
                plan.append("Execute calculator tool")
                plan.append("Format calculation result")
            
            elif output.primary_action == ActionType.SEARCH_PRODUCTS:
                plan.append("Execute vector search for products")
                plan.append("Format product results with prices and capacities")
                plan.append("Generate AI summary of products")
            
            elif output.primary_action == ActionType.SEARCH_OUTLETS:
                plan.append("Execute text-to-SQL for outlet search")
                plan.append("Include maps_url in results if location query")
                plan.append("Format outlet results with addresses")
            
            elif output.primary_action == ActionType.HYBRID_SEARCH:
                plan.append("Execute both product and outlet searches")
                plan.append("Combine results in coherent response")
            
            elif output.primary_action == ActionType.CONVERSATIONAL:
                plan.append("Use conversation context for response")
                plan.append("Provide helpful general information")
            
            # Add secondary actions
            for secondary in output.secondary_actions:
                plan.append(f"Also execute: {secondary.value}")
        
        return plan


# Global planner instance
_planner = None

def get_planner() -> AgenticPlanner:
    """Get or create global planner instance"""
    global _planner
    if _planner is None:
        _planner = AgenticPlanner()
    return _planner
