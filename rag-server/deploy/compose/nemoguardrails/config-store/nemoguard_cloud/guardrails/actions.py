from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
import logging

logger = logging.getLogger(__name__)


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
async def quiz_response(context, **kwargs):
    logger.error(f"QUIZ RESPONSE ACTION TRIGGERED! kwargs: {kwargs}")
    return "This is a test response from the quiz_response action."