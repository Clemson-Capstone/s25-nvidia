import logging
from typing import Dict, List, Optional

from langchain_core.language_models.llms import BaseLLM

from nemoguardrails.actions import action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.llm.filters import to_chat_messages
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.logging.explain import LLMCallInfo
from nemoguardrails import LLMRails, RailsConfig


logger = logging.getLogger(__name__)

logger.error(f"Your in the actions file")
# Define the quiz response prompt template
quiz_response_template = """
        Based on the following quiz question, DO NOT provide or hint at the correct answer.
        Instead, explain the underlying concepts to help understanding.
        
        Question: {question}
        
        Format your response exactly as follows (preserve all newlines and spacing):
        
        Key Concept 1
        
        Key Concept 2
        
        Practical Application
        
        Brief explanation connecting the concepts.
        """


@action(is_system_action=False)
async def quiz_response():
    logger.error(f"QUIZ RESPONSE ACTION TRIGGERED!")
    return "This is a test response from the quiz_response action."

@action(is_system_action=False)
async def homework_brainstorm():
    logger.error(f"Homework RESPONSE ACTION TRIGGERED!")
    return "Just testing from the homework action."

@action(is_system_action=False)
async def code_debug():
    logger.error(f"Homework RESPONSE ACTION TRIGGERED!")
    return "Just testing from the code debug action."

# This portion was how we initally initialized our python actions in rag 1.0


def init(app):
    # Check if it's a FastAPI app or LLMRails
    if hasattr(app, "register_action"):
        app.register_action(quiz_response, "quiz_response")
        app.register_action(homework_brainstorm,"homework_brainstorm")
        app.register_action(code_debug, "code_debug")
    else:
        # If it's a FastAPI app, you might need to initialize rails differently
        from nemoguardrails import LLMRails, RailsConfig
        config = RailsConfig.from_path("/config-store/nemoguard_cloud")
        rails = LLMRails(config)
        rails.register_action(quiz_response, "quiz_response")
        rails.register_action(homework_brainstorm,"homework_brainstorm")
        rails.register_action(code_debug, "code_debug")



# @action(is_system_action=False)
# async def quiz_response():
#     logger.error(f"QUIZ RESPONSE ACTION TRIGGERED!")
#     return "This is a test response from the quiz_response action."

# # This portion was how we initally initialized our python actions in rag 1.0


# def init(app):
#     # Check if it's a FastAPI app or LLMRails
#     if hasattr(app, "register_action"):
#         app.register_action(quiz_response, "quiz_response")
#     else:
#         # If it's a FastAPI app, you might need to initialize rails differently
#         from nemoguardrails import LLMRails, RailsConfig
#         config = RailsConfig.from_path("/config-store/nemoguard_cloud")
#         rails = LLMRails(config)
#         rails.register_action(quiz_response, "quiz_response")
        # Then attach rails to your FastAPI app somehow
# @action
# async def quiz_response(inputs: str):
#     logger.error(f"QUIZ RESPONSE ACTION TRIGGERED!")
#     print("Hello the aciton is working")
#     return "This is a test response from the quiz_response action."

# # This portion was how we initally initialized our python actions in rag 1.0



# def init(llm_rails: LLMRails):

#     # # Initialize rails config 
#     config = RailsConfig.from_path("/config-store/nemoguard_cloud")
#     # Create rails

#     rails = LLMRails(config)

#     rails.register_action(quiz_response, "quiz_response")

    # Register the custom `retrieve_relevant_chunks` for custom retrieval
    # llm_rails.register_action(quiz_response, "quiz_response")