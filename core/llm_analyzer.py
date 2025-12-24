"""LLM-powered resume analysis service."""
from typing import Dict, List
from config import settings


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
                    {"role": "system", "content": "You are an expert resume analyst and HR professional."},
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
        """Build comprehensive analysis prompt."""
        
        base_prompt = f"""Analyze this resume comprehensively:

RESUME:
{resume_text[:2000]}

Provide structured analysis with:
1. **Strengths**: Key qualifications and achievements
2. **Experience Level**: Years and seniority assessment
3. **Technical Skills**: Identified technical competencies
4. **Soft Skills**: Identified soft skills
5. **Career Trajectory**: Career path analysis
6. **Gaps**: Potential gaps or improvements
7. **Score**: Overall resume quality (0-100)
8. **Recommendations**: Specific improvements

Be concise and actionable."""
        
        if job_description:
            base_prompt += f"\n\nJOB DESCRIPTION:\n{job_description[:1000]}\n\nAlso assess fit for this role."
        
        return base_prompt
    
    @staticmethod
    def _parse_analysis(analysis_text: str) -> Dict:
        """Parse LLM response into structured format."""
        return {
            "raw_analysis": analysis_text,
            "sections": analysis_text.split('\n\n'),
        }
