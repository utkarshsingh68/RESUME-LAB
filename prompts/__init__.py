"""Load system prompts for LLM operations."""
from pathlib import Path


def load_system_prompt() -> str:
    """Load the AI Career Coach system prompt."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
    
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    
    # Fallback if file doesn't exist
    return "You are an expert AI Career Coach, ATS Resume Evaluator, and Job Matcher with deep knowledge of hiring standards and applicant tracking systems."


CAREER_COACH_PROMPT = load_system_prompt()
