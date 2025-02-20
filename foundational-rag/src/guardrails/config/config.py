# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from datetime import datetime
from typing import Optional

from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import BaseLLM
from langchain_core.output_parsers import StrOutputParser

from nemoguardrails import LLMRails
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.llm.taskmanager import LLMTaskManager


# Define the quiz response prompt template
quiz_response_template = """
Based on the following quiz question, DO NOT provide or hint at the correct answer.
Instead, explain the underlying concepts to help understanding.

Question: {question}

Concept Explanation (no answers):
"""

@action(is_system_action=False)
async def quiz_response(context: dict, llm: BaseLLM):
    log.info("QUIZ RESPONSE ACTION TRIGGERED!")
    try:
        # Get the quiz question from the context
        inputs = context.get("last_user_message")
        log.info(f"Processing quiz question: {inputs}")
        
        # Build the prompt chain
        output_parser = StrOutputParser()
        prompt_template = PromptTemplate.from_template(quiz_response_template)
        input_variables = {"question": inputs}
        chain = prompt_template | llm | output_parser
        
        # Invoke the chain to generate a response
        answer = await chain.ainvoke(input_variables)
        log.info(f"Generated quiz response: {answer}")
        
        # Return an ActionResult with the answer and any context updates (if needed)
        return ActionResult(
            return_value="I understand you're asking about: " + answer,
            context_updates={}
        )
    except Exception as e:
        log.error(f"Error in quiz_response: {e}")
        return ActionResult(
            return_value="I can help explain the concepts, but I cannot provide direct answers to quiz questions.",
            context_updates={}
        )

def init(app: LLMRails):
    # Register the quiz_response action with the key "quiz_response"
    print("Initializing actions from config.py")  # Temporary debug line
    app.register_action(quiz_response, "quiz_response")