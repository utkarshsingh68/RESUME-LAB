"""LLM-powered resume analysis service."""
from typing import Dict, List
from config import settings
from prompts import CAREER_COACH_PROMPT


class ResumeLLMAnalyzer:
    """Production-grade LLM analyzer for resume insights."""
    
    def __init__(self):
        """Initialize LLM client."""
        try:
            import openai
            if settings.LLM_BASE_URL:
                self.client = openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.LLM_BASE_URL
                )
            else:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            raise ImportError("Install openai: pip install openai")
    
    def analyze_resume(self, resume_text: str, job_description: str = None) -> Dict:
        """Comprehensive AI-powered resume analysis."""
        
        prompt = self._build_analysis_prompt(resume_text, job_description)
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": CAREER_COACH_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            
            analysis_text = response.choices[0].message.content
            return self._parse_analysis(analysis_text)
        
        except Exception as e:
            return {"error": str(e), "analysis": None}
    
    def match_resume_to_job(self, resume_text: str, job_description: str) -> Dict:
        """Calculate resume-to-job match score and feedback."""
        
        prompt = f"""Analyze the following resume against the job description.

RESUME:
{resume_text[:2000]}

JOB DESCRIPTION:
{job_description[:2000]}

Provide:
1. Match Score (0-100)
2. Key Strengths for this role
3. Missing Skills
4. Recommendations for improvement

Format as JSON."""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert recruiter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000,
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
        
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def _build_analysis_prompt(resume_text: str, job_description: str = None) -> str:
        """Build comprehensive analysis prompt following AI Career Coach format."""
        
        base_prompt = f"""RESUME TEXT:
{resume_text[:2500]}

Please provide a comprehensive analysis following this exact structure:

## Resume Summary
Brief overview of the candidate's profile, experience level, and primary domain.

## ATS Score
Overall compatibility score (0-100) and detailed breakdown.

## Strengths
What's working well in this resume (bullet points).

## Skill Gaps
Missing or weak areas with clear explanations.

## Improved Resume Suggestions
Concrete improvements with rewritten bullet points using strong action verbs and measurable outcomes.

## Job Role Recommendations
Suitable positions based on this profile.

## Interview Preparation
Key interview questions for their target roles.

## Next Action Steps
Prioritized tasks to improve candidacy.

Be specific, actionable, and data-driven."""
        
        if job_description:
            base_prompt += f"\n\nTARGET JOB DESCRIPTION:\n{job_description[:1500]}\n\nCalculate detailed ATS match score based on skill overlap, keyword relevance, experience alignment, and role fit."
        
        return base_prompt
    
    @staticmethod
    def _parse_analysis(analysis_text: str) -> Dict:
        """Parse LLM response into structured format."""
        return {
            "raw_analysis": analysis_text,
            "sections": analysis_text.split('\n\n'),
        }
