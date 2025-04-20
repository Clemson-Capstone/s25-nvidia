import logging
from typing import Dict, List, Optional

from langchain_core.language_models.llms import BaseLLM

from langchain_core.output_parsers.string import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import BaseLLM

from langchain_core.output_parsers.string import StrOutputParser

from nemoguardrails.actions import action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.llm.filters import to_chat_messages
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.logging.explain import LLMCallInfo
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.actions import ActionResult

logger = logging.getLogger(__name__)

logger.error(f"Your in the actions file")
# Define the quiz response prompt template



@action(is_system_action=False)
async def quiz_response(context: dict, llm: BaseLLM = None):
    logger.error(f"QUIZ RESPONSE ACTION TRIGGERED!")
    try:
        # Get the user's message from the context
        user_message = context.get("last_user_message", "")
        
        if not user_message:
            return ActionResult(
                return_value="I couldn't understand your code issue. Could you please provide more details?",
                context_updates={}
            )
        
        # Now that you have the user's message, use it with the LLM
        if llm:
            # Create a template for code debugging
            quiz_response_template = """
            Based on the following quiz question, DO NOT provide or hint at the correct answer.
            Instead, explain the underlying concepts to help understanding.
            
            Do NOT give the answer. Instead, explain the key concepts involved in a short and informative paragraph. Your response should help the student understand the *why* and *how* behind the question without solving it.

            Keep the response concise, natural, and focused on clarification, like you're coaching the student through the thought process.
            """
            
            # Import the necessary modules
            
            # Create the prompt chain
            prompt_template = PromptTemplate.from_template(quiz_response_template)
            chain = prompt_template | llm | StrOutputParser()
            
            # Generate the response
            answer = await chain.ainvoke({"question": user_message})
            
            return ActionResult(
                return_value=answer,
                context_updates={}
            )
        else:
            return ActionResult(
                return_value="I'd suggest breaking down this problem into smaller parts and identifying the key concepts involved. What specific aspect are you finding challenging?",
                context_updates={}
            )
    except Exception as e:
        logger.error(f"Error in quiz response: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ActionResult(
            return_value="I encountered an error while generating the quiz response. Could you please provide more details about your issue?",
            context_updates={}
        )
    

@action(is_system_action=False)
async def homework_brainstorm(context: dict, llm: BaseLLM = None):
    logger.error(f"Homework RESPONSE ACTION TRIGGERED!")
    try:
        # Get the user's message from the context
        user_message = context.get("last_user_message", "")
        
        if not user_message:
            return ActionResult(
                return_value="I couldn't understand your code issue. Could you please provide more details?",
                context_updates={}
            )
        
        # Now that you have the user's message, use it with the LLM
        if llm:
            # Create a template for code debugging
            homework_brainstorm_template = """
            For this homework question, provide a structured brainstorming approach that helps the student develop their own solution. Include:

            1. A breakdown of the key concepts involved
            2. Multiple approaches or methodologies to consider
            3. Relevant examples that illustrate the concepts (without solving the exact problem)
            4. Questions the student should ask themselves while working
            5. Resources they might consult for deeper understanding

            Question: {question}

            Brainstorming guidance (do not solve directly):
            """
            
            # Import the necessary modules
            
            # Create the prompt chain
            prompt_template = PromptTemplate.from_template(homework_brainstorm_template)
            chain = prompt_template | llm | StrOutputParser()
            
            # Generate the response
            answer = await chain.ainvoke({"question": user_message})
            
            return ActionResult(
                return_value=answer,
                context_updates={}
            )
        else:
            return ActionResult(
                return_value="I'd suggest breaking down this problem into smaller parts and identifying the key concepts involved. What specific aspect are you finding challenging?",
                context_updates={}
            )
    except Exception as e:
        logger.error(f"Error in homework_brainstorm: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ActionResult(
            return_value="I encountered an error while analyzing your code. Could you please provide more details about your issue?",
            context_updates={}
        )

@action(is_system_action=False)
async def code_debug(context: dict, llm: BaseLLM = None):
    """Debug code issues for students."""
    logger.info("CODE DEBUG ACTION TRIGGERED!")
    try:
        # Get the user's message from the context
        user_message = context.get("last_user_message", "")
        
        if not user_message:
            return ActionResult(
                return_value="I couldn't understand your code issue. Could you please provide more details?",
                context_updates={}
            )
        
        # Now that you have the user's message, use it with the LLM
        if llm:
            # Create a template for code debugging
            code_debug_template = """
            Based on the code debugging question provided, DO NOT provide the exact solution or directly fix the code.
            Instead, help guide the student through a debugging process by:
            1. Explaining relevant programming concepts
            2. Suggesting areas to investigate
            3. Providing general debugging strategies
            4. Asking guiding questions that help them discover the issue themselves

            Question: {question}

            Helpful debugging guidance (no direct solutions):
            """
            
            # Import the necessary modules
            
            # Create the prompt chain
            prompt_template = PromptTemplate.from_template(code_debug_template)
            chain = prompt_template | llm | StrOutputParser()
            
            # Generate the response
            answer = await chain.ainvoke({"question": user_message})
            
            return ActionResult(
                return_value=answer,
                context_updates={}
            )
        else:
            return ActionResult(
                return_value="I can help you debug your code, but I need access to advanced capabilities. Please try again later.",
                context_updates={}
            )
    except Exception as e:
        logger.error(f"Error in code_debug: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ActionResult(
            return_value="I encountered an error while analyzing your code. Could you please provide more details about your issue?",
            context_updates={}
        )



# List of blocked (non-academic) keywords
# BLOCKED_KEYWORDS = [
#     "election", "politics", "religion", "opinion", "government", "president",
#     "war", "economy", "racism", "gender", "news", "conspiracy"
# ]

# @action(is_system_action=False)
# async def ta_response(context: dict, llm=None):
#     logger.info("TA CONTEXT CHECK ACTION TRIGGERED")

#     user_message = context.get("last_user_message", "").lower().strip()

#     if not user_message:
#         return ActionResult(
#             return_value="Can you clarify your question? I'm here to help with course-related topics.",
#             context_updates={}
#         )

#     if any(blocked in user_message for blocked in BLOCKED_KEYWORDS):
#         return ActionResult(
#             return_value="I am not allowed to respond to that, sorry (self_check_input hit)",
#             context_updates={}
#         )

#     return ActionResult(
#         return_value="Thanks for your question! Let me know if it's related to any course material, and I'll do my best to assist.",
#         context_updates={}
#     )

def init(app):
    # Check if it's a FastAPI app or LLMRails
    if hasattr(app, "register_action"):
        app.register_action(quiz_response, "quiz_response")
        app.register_action(homework_brainstorm,"homework_brainstorm")
        app.register_action(code_debug, "code_debug")
        # app.register_action(ta_response, "ta_response")
    else:
        # If it's a FastAPI app, you might need to initialize rails differently
        from nemoguardrails import LLMRails, RailsConfig
        config = RailsConfig.from_path("/config-store/nemoguard_cloud")
        rails = LLMRails(config)
        rails.register_action(quiz_response, "quiz_response")
        rails.register_action(homework_brainstorm,"homework_brainstorm")
        rails.register_action(code_debug, "code_debug")
        # rails.register_action(ta_response, "ta_response")
    


