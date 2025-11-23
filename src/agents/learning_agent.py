"""Learning Agent implementation using AWS Bedrock AgentCore and Strand Agent pattern."""

import json
from enum import Enum
from typing import Any

from src.services import BedrockService
from src.utils import AgentExecutionError, get_logger

from .strand_agent import StrandAgent, StrandContext

logger = get_logger(__name__)


class LearningGoal(str, Enum):
    """Learning goals supported by the agent."""

    CONCEPT_EXPLANATION = "concept_explanation"
    PROBLEM_SOLVING = "problem_solving"
    CODE_REVIEW = "code_review"
    GUIDED_PRACTICE = "guided_practice"
    ASSESSMENT = "assessment"
    PERSONALIZED_LEARNING_PATH = "personalized_learning_path"


class LearningAgent(StrandAgent):
    """Learning Agent that provides personalized educational assistance.

    This agent uses AWS Bedrock AgentCore capabilities and implements the Strand Agent
    pattern for multi-step learning interactions.
    """

    def __init__(self, bedrock_service: BedrockService | None = None) -> None:
        """Initialize learning agent.

        Args:
            bedrock_service: Optional BedrockService instance
        """
        super().__init__(bedrock_service)
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the learning agent."""
        return """You are an advanced AI Learning Assistant powered by AWS Bedrock. Your role is to provide
personalized, adaptive educational support to learners of all levels.

Core Capabilities:
1. Concept Explanation: Break down complex topics into digestible parts
2. Problem Solving: Guide learners through problem-solving processes
3. Code Review: Analyze and provide constructive feedback on code
4. Guided Practice: Offer step-by-step practice exercises
5. Assessment: Evaluate understanding and provide feedback
6. Personalized Learning Paths: Create customized learning journeys

Principles:
- Adapt to the learner's level and pace
- Use the Socratic method when appropriate
- Provide clear, concrete examples
- Encourage critical thinking and self-discovery
- Give constructive, actionable feedback
- Break complex topics into manageable chunks
- Validate understanding before moving forward

Communication Style:
- Clear, concise, and encouraging
- Use analogies and real-world examples
- Ask probing questions to assess understanding
- Celebrate progress and provide positive reinforcement

When responding:
1. First, understand the learner's current level and goal
2. Assess what they already know
3. Provide targeted instruction or guidance
4. Check for understanding
5. Adjust approach based on their responses
"""

    async def process_step(self, context: StrandContext) -> StrandContext:
        """Process a single learning interaction step.

        Args:
            context: Current strand context

        Returns:
            Updated context with agent response

        Raises:
            AgentExecutionError: If processing fails
        """
        try:
            # Get the latest user message
            user_messages = [msg for msg in context.messages if msg.role == "user"]
            if not user_messages:
                raise AgentExecutionError(
                    "No user message found in context",
                    details={"strand_id": context.strand_id},
                )

            latest_message = user_messages[-1].content

            # Determine learning goal if not set
            if "learning_goal" not in context.variables:
                context.variables["learning_goal"] = await self._identify_learning_goal(latest_message)

            learning_goal = context.variables["learning_goal"]

            self.logger.info(
                "Processing learning step",
                strand_id=context.strand_id,
                learning_goal=learning_goal,
                iteration=context.iteration,
            )

            # Build context-aware prompt
            prompt = self._build_learning_prompt(context, latest_message, learning_goal)

            # Invoke model with system prompt
            response = await self.invoke_model(
                prompt=prompt,
                system_prompt=self.system_prompt,
                context=context,
            )

            # Add agent response to context
            context.add_message(
                "assistant",
                response,
                metadata={"learning_goal": learning_goal, "iteration": context.iteration},
            )

            # Update learning progress
            await self._update_learning_progress(context, response)

            return context

        except Exception as e:
            self.logger.error("Failed to process learning step", error=str(e))
            raise AgentExecutionError(
                f"Failed to process learning step: {e}",
                details={"strand_id": context.strand_id, "error": str(e)},
            )

    def should_continue(self, context: StrandContext) -> bool:
        """Determine if learning session should continue.

        Args:
            context: Current strand context

        Returns:
            True if should continue, False otherwise
        """
        # Continue if we haven't reached conclusion
        if "learning_complete" in context.variables:
            return not context.variables["learning_complete"]

        # Check if last assistant message indicates completion
        assistant_messages = [msg for msg in context.messages if msg.role == "assistant"]
        if assistant_messages:
            last_response = assistant_messages[-1].content.lower()

            # Look for completion indicators
            completion_phrases = [
                "learning session complete",
                "you've mastered",
                "congratulations on completing",
                "assessment complete",
            ]

            if any(phrase in last_response for phrase in completion_phrases):
                context.variables["learning_complete"] = True
                return False

        # Continue if under max iterations
        return context.iteration < context.max_iterations

    async def _identify_learning_goal(self, user_input: str) -> str:
        """Identify the learning goal from user input.

        Args:
            user_input: User's input message

        Returns:
            Identified learning goal
        """
        # Simple keyword-based identification (can be enhanced with ML)
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["explain", "what is", "how does", "understand"]):
            return LearningGoal.CONCEPT_EXPLANATION.value
        elif any(word in user_input_lower for word in ["solve", "problem", "help me with"]):
            return LearningGoal.PROBLEM_SOLVING.value
        elif any(word in user_input_lower for word in ["review", "feedback", "look at my code"]):
            return LearningGoal.CODE_REVIEW.value
        elif any(word in user_input_lower for word in ["practice", "exercise", "quiz"]):
            return LearningGoal.GUIDED_PRACTICE.value
        elif any(word in user_input_lower for word in ["test", "assess", "evaluate"]):
            return LearningGoal.ASSESSMENT.value
        elif any(word in user_input_lower for word in ["learn", "study plan", "roadmap"]):
            return LearningGoal.PERSONALIZED_LEARNING_PATH.value
        else:
            return LearningGoal.CONCEPT_EXPLANATION.value

    def _build_learning_prompt(
        self,
        context: StrandContext,
        user_message: str,
        learning_goal: str,
    ) -> str:
        """Build a context-aware learning prompt.

        Args:
            context: Strand context
            user_message: Latest user message
            learning_goal: Current learning goal

        Returns:
            Formatted prompt
        """
        # Include conversation history for context
        history = ""
        if len(context.messages) > 1:
            history = "\n\nConversation History:\n"
            for msg in context.messages[-5:]:  # Last 5 messages for context
                history += f"{msg.role.upper()}: {msg.content}\n"

        # Build prompt based on learning goal
        goal_context = f"\nLearning Goal: {learning_goal}\n"

        # Add learner profile if available
        profile_context = ""
        if "learner_level" in context.variables:
            profile_context = f"\nLearner Level: {context.variables['learner_level']}\n"

        if "learning_preferences" in context.variables:
            profile_context += f"Learning Preferences: {context.variables['learning_preferences']}\n"

        prompt = f"""{goal_context}{profile_context}{history}

Current User Input: {user_message}

Please provide a response that:
1. Addresses the user's specific question or need
2. Is appropriate for their learning goal: {learning_goal}
3. Builds on the conversation history
4. Checks for understanding when appropriate
5. Provides next steps or asks clarifying questions

Response:"""

        return prompt

    async def _update_learning_progress(self, context: StrandContext, response: str) -> None:
        """Update learning progress based on interaction.

        Args:
            context: Strand context
            response: Agent's response
        """
        # Initialize progress tracking if not exists
        if "progress" not in context.variables:
            context.variables["progress"] = {
                "topics_covered": [],
                "questions_asked": 0,
                "concepts_explained": 0,
                "problems_solved": 0,
            }

        progress = context.variables["progress"]

        # Update counters based on response content
        if "?" in response:
            progress["questions_asked"] += 1

        # Check for learning completion indicators
        if any(
            phrase in response.lower()
            for phrase in ["you understand", "well done", "excellent work", "mastered"]
        ):
            context.variables["comprehension_level"] = context.variables.get("comprehension_level", 0) + 1

    async def get_learning_summary(self, context: StrandContext) -> dict[str, Any]:
        """Generate a learning summary from the context.

        Args:
            context: Strand context

        Returns:
            Learning summary dictionary
        """
        summary = {
            "session_id": context.session_id,
            "strand_id": context.strand_id,
            "learning_goal": context.variables.get("learning_goal", "unknown"),
            "total_interactions": len(context.messages) // 2,  # User + Assistant pairs
            "duration_seconds": None,
            "progress": context.variables.get("progress", {}),
            "topics_covered": context.variables.get("topics_covered", []),
            "learning_complete": context.variables.get("learning_complete", False),
        }

        if context.start_time and context.end_time:
            duration = (context.end_time - context.start_time).total_seconds()
            summary["duration_seconds"] = duration

        return summary

    async def ask_question(self, question: str, session_id: str | None = None) -> dict[str, Any]:
        """Ask a single question to the learning agent.

        Args:
            question: User's question
            session_id: Optional session ID for continuing a conversation

        Returns:
            Response dictionary with answer and context
        """
        # Create or retrieve context
        context = None
        if session_id and hasattr(self, "_active_contexts"):
            context = self._active_contexts.get(session_id)

        # Execute the agent
        result_context = await self.execute(question, context=context)

        # Store context for session continuity
        if not hasattr(self, "_active_contexts"):
            self._active_contexts: dict[str, StrandContext] = {}
        self._active_contexts[result_context.session_id] = result_context

        # Get the latest assistant response
        assistant_messages = [msg for msg in result_context.messages if msg.role == "assistant"]
        latest_response = assistant_messages[-1] if assistant_messages else None

        return {
            "answer": latest_response.content if latest_response else "",
            "session_id": result_context.session_id,
            "strand_id": result_context.strand_id,
            "learning_goal": result_context.variables.get("learning_goal"),
            "iteration": result_context.iteration,
            "complete": result_context.variables.get("learning_complete", False),
        }

    async def review_code(self, code: str, language: str, context_description: str = "") -> str:
        """Review code and provide educational feedback.

        Args:
            code: Code to review
            language: Programming language
            context_description: Optional context about the code

        Returns:
            Detailed code review with educational insights
        """
        prompt = f"""Please review the following {language} code and provide educational feedback:

Context: {context_description if context_description else 'No additional context provided'}

Code:
```{language}
{code}
```

Please provide:
1. What the code does well
2. Areas for improvement with explanations
3. Best practices that should be applied
4. Learning opportunities and concepts to study
5. Refactoring suggestions with educational rationale
"""

        response = await self.invoke_model(prompt=prompt, system_prompt=self.system_prompt)
        return response

    async def create_learning_path(
        self,
        topic: str,
        current_level: str,
        target_level: str,
        time_commitment: str,
    ) -> dict[str, Any]:
        """Create a personalized learning path.

        Args:
            topic: Learning topic
            current_level: Current skill level (beginner/intermediate/advanced)
            target_level: Target skill level
            time_commitment: Available time commitment

        Returns:
            Structured learning path
        """
        prompt = f"""Create a personalized learning path for the following:

Topic: {topic}
Current Level: {current_level}
Target Level: {target_level}
Time Commitment: {time_commitment}

Please provide a structured learning path in JSON format with:
1. Overall learning objectives
2. Phases/milestones
3. Topics to cover in each phase
4. Recommended resources
5. Practice exercises
6. Assessment criteria
7. Estimated timeline

Format the response as valid JSON.
"""

        response = await self.invoke_model(prompt=prompt, system_prompt=self.system_prompt)

        # Try to parse JSON response
        try:
            learning_path = json.loads(response)
        except json.JSONDecodeError:
            # If not valid JSON, return structured response
            learning_path = {
                "topic": topic,
                "current_level": current_level,
                "target_level": target_level,
                "time_commitment": time_commitment,
                "plan": response,
            }

        return learning_path
