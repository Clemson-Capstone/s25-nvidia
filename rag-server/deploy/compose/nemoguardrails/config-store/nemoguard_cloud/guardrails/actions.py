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

@action
async def quiz_response(inputs: str):
    logger.error(f"QUIZ RESPONSE ACTION TRIGGERED!")
    return "This is a test response from the quiz_response action."

# This portion was how we initally initialized our python actions in rag 1.0

# # Initialize rails config 
config = RailsConfig.from_path("/config-store/nemoguard_cloud/guardrails")
# Create rails

rails = LLMRails(config)

rails.register_action(quiz_response, "quiz_response")
