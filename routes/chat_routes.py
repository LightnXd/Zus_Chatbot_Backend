"""
Chat endpoint route handler
"""
import logging
import uuid
from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Optional

from conversation_memory import get_memory_manager
from agentic_planner import get_planner, ActionType
from calculator_tool import get_calculator
from services.product_service import retrieve_products
from services.outlet_service import get_outlet_info, count_outlets_from_response
from config.app_config import SYSTEM_TEMPLATE

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    products_found: int
    outlets_found: int
    search_info: dict
    session_id: str
    planning_info: Optional[dict] = None

async def handle_chat(request: ChatRequest, model, retriever, text_to_sql, outlet_queries):
    """Main chat endpoint handler with conversation memory and agentic planning"""
    try:
        if not model:
            raise HTTPException(status_code=500, detail="LLM not initialized")
        
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        memory = get_memory_manager()
        
        # Get conversation history and context
        conversation_history = memory.get_conversation_context(session_id, n=3)
        context_metadata = memory.get_context_metadata(session_id)
        
        logger.info(f"📝 Session: {session_id}")
        logger.info(f"📚 Conversation history: {len(conversation_history)} characters")
        logger.info(f"🔍 Context metadata: {context_metadata}")
        
        # AGENTIC PLANNER - Make explicit decisions with reasoning
        planner = get_planner()
        plan = planner.plan(question, conversation_context={'metadata': context_metadata})
        
        # Planning decisions logging removed - now returned in planning_info for frontend display
        
        # Use planner decisions for routing
        search_products = plan.primary_action in [ActionType.SEARCH_PRODUCTS, ActionType.HYBRID_SEARCH]
        search_outlets = plan.primary_action in [ActionType.SEARCH_OUTLETS, ActionType.HYBRID_SEARCH]
        do_calculation = plan.primary_action == ActionType.CALCULATE
        
        # Also enable searches if they're secondary actions with good confidence
        for decision in plan.decisions:
            if decision.action == ActionType.SEARCH_PRODUCTS and decision.confidence > 0.4:
                search_products = True
            if decision.action == ActionType.SEARCH_OUTLETS and decision.confidence > 0.4:
                search_outlets = True
            if decision.action == ActionType.CALCULATE and decision.confidence > 0.5:
                do_calculation = True
        
        logger.info(f"Search routing (planner-driven) - Products: {search_products}, Outlets: {search_outlets}, Calculate: {do_calculation}")
        
        # Perform calculation if needed
        calculation_result = None
        if do_calculation:
            try:
                calculator = get_calculator()
                calc_data = calculator.parse_and_calculate(question)
                calculation_result = calc_data
                logger.info(f"🧮 Calculation result: {calc_data}")
            except Exception as e:
                logger.error(f"Error in calculation: {e}")
                calculation_result = {
                    "success": False,
                    "error": f"Calculation failed: {str(e)}"
                }
        
        # Retrieve products
        drinkware = "Not requested"
        products_found = 0
        if search_products:
            drinkware, products_found = retrieve_products(question, retriever)
        
        # Retrieve outlets
        outlet_info = "Not requested"
        outlets_found = 0
        if search_outlets:
            outlet_info = get_outlet_info(question, text_to_sql, outlet_queries)
            logger.info(f"Outlet info returned: {outlet_info[:200]}...")
            outlets_found = count_outlets_from_response(outlet_info)
            logger.info(f"✅ Outlets found: {outlets_found}")
        
        # Add user message to conversation history
        memory.add_user_message(
            session_id,
            question,
            metadata={
                "searched_products": search_products,
                "searched_outlets": search_outlets,
                "planner_action": plan.primary_action.value
            }
        )
        
        # Create prompt - add clarification questions if needed
        if plan.should_ask_clarification and plan.clarification_questions:
            logger.info(f"❓ Asking {len(plan.clarification_questions)} clarification questions")
            
            # Add clarification context to the system
            clarification_context = "\n\nCLARIFICATION NEEDED:\n" + "\n".join([
                f"- {q}" for q in plan.clarification_questions
            ])
            
            prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE + clarification_context)
        else:
            # Add calculation result to system template if available
            if calculation_result and calculation_result.get("success"):
                calc_context = f"\n\nCALCULATION RESULT:\n{calculation_result.get('formatted', '')}\n\nIMPORTANT: Keep your response BRIEF (1-2 sentences). Simply state the answer and ask if they have any other questions or need help with products/outlets."
                prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE + calc_context)
            elif calculation_result and not calculation_result.get("success"):
                calc_context = f"\n\nCALCULATION ERROR:\n{calculation_result.get('error', 'Unknown error')}\n\nIMPORTANT: Keep your response BRIEF (1-2 sentences). Explain the error simply and ask if they have any other questions or need help with products/outlets."
                prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE + calc_context)
            else:
                prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)
        
        chain = prompt | model
        
        # Generate response
        result = chain.invoke({
            "conversation_history": conversation_history,
            "drinkware": drinkware or "No products found",
            "outlet": outlet_info or "No outlets found",
            "question": question,
        })
        
        # Extract response content
        response_text = result.content if hasattr(result, 'content') else str(result)
        
        # If clarification was needed, append follow-up questions
        if plan.should_ask_clarification and plan.clarification_questions:
            # Only add if LLM didn't already ask similar questions
            if "?" not in response_text[-100:]:  # Check last 100 chars
                response_text += "\n\n" + "\n".join(plan.clarification_questions)
        
        # Add assistant response to conversation history
        memory.add_assistant_message(
            session_id,
            response_text,
            metadata={
                "products_found": products_found,
                "outlets_found": outlets_found,
                "clarification_asked": plan.should_ask_clarification
            }
        )
        
        # Build planning info for response
        planning_info = {
            "primary_action": plan.primary_action.value,
            "secondary_actions": [a.value for a in plan.secondary_actions],
            "decision_count": len(plan.decisions),
            "decisions": plan.get_decision_log(),
            "execution_plan": plan.execution_plan,
            "clarification_needed": plan.should_ask_clarification,
            "clarification_questions": plan.clarification_questions,
            "calculation_performed": calculation_result is not None,
            "calculation_result": calculation_result if calculation_result else None
        }
        
        return ChatResponse(
            response=response_text,
            products_found=products_found,
            outlets_found=outlets_found,
            search_info={
                "searched_products": search_products,
                "searched_outlets": search_outlets,
                "mode": plan.primary_action.value,
                "has_conversation_history": conversation_history != "No previous conversation.",
                "context_metadata": context_metadata
            },
            session_id=session_id,
            planning_info=planning_info
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
