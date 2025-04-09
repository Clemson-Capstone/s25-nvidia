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

@action(is_system_action=True)
async def quiz_response(context: dict, llm: BaseLLM):
    logger.info("QUIZ RESPONSE ACTION TRIGGERED!")
    try:
        # Get the quiz question from the context
        inputs = context.get("last_user_message")
        logger.info(f"Processing quiz question: {inputs}")
        
        # Build the prompt chain
        output_parser = StrOutputParser()
        prompt_template = PromptTemplate.from_template(quiz_response_template)
        input_variables = {"question": inputs}
        chain = prompt_template | llm | output_parser
        
        # Invoke the chain to generate a response
        raw_documents = UnstructuredLoader(_path).load()
        formatted_answer = raw_answer.replace("\n\n", "<br><br>").replace("\n", "<br>")
        logger.info(f"Generated quiz response: {formatted_answer}")
        
        # Return an ActionResult with the answer and any context updates (if needed)
        return ActionResult(
            return_value="I understand you're asking about: " + formatted_answer,
            context_updates={}
        )
    except Exception as e:
        logger.error(f"Error in quiz_response: {e}")
        return ActionResult(
            return_value="I can help explain the concepts, but I cannot provide direct answers to quiz questions.",
            context_updates={}
        )