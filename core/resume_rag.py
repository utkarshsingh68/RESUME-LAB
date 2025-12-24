"""
Retrieval-Augmented Generation (RAG) system for resume chat.
Enables conversational interaction with resume content.
"""
from typing import List, Dict, Tuple
import json
import logging
from config import settings


logger = logging.getLogger(__name__)


class ResumeRAG:
    """RAG system for context-aware resume questions."""
    
    def __init__(self, vector_store, embedding_service, llm_analyzer):
        """Initialize RAG components."""
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm_analyzer = llm_analyzer
    
    def answer_question(self, resume_id: str, question: str) -> Dict:
        """Answer question based on resume context using RAG."""
        try:
            # Retrieve relevant resume chunks
            query_embedding = self.embedding_service.embed_text(question)
            context_results = self.vector_store.search(query_embedding, k=3)
            
            if not context_results:
                return {
                    "answer": "I don't have enough information in the resume to answer this question.",
                    "confidence": 0.0,
                    "sources": []
                }
            
            # Build context from retrieved chunks
            context = self._build_context(context_results)
            
            # Generate answer using LLM with retrieved context
            answer = self._generate_answer(question, context)
            
            # Extract sources
            sources = [result[1].get("text", "") for result in context_results[:2]]
            
            return {
                "answer": answer,
                "confidence": self._calculate_confidence(context_results),
                "sources": sources,
                "retrieved_count": len(context_results)
            }
        except Exception:
            logger.exception("Failed to answer resume question for %s", resume_id)
            raise
    
    @staticmethod
    def _build_context(results: List[Tuple[float, Dict]]) -> str:
        """Build context string from retrieved results."""
        context_parts = []
        for score, metadata in results:
            context_parts.append(f"[Relevance: {score:.1%}]\n{metadata.get('text', '')}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with context."""
        prompt = f"""Answer the following question strictly based on the resume context provided.
If the information is not in the resume, say "This information is not available in the resume."

RESUME CONTEXT:
{context}

QUESTION: {question}

ANSWER (concise, factual, based only on the provided context):"""
        
        try:
            response = self.llm_analyzer.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions about resumes based only on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Unable to generate answer: {str(e)}"
    
    @staticmethod
    def _calculate_confidence(results: List[Tuple[float, Dict]]) -> float:
        """Calculate confidence score based on retrieval scores."""
        if not results:
            return 0.0
        
        avg_score = sum(r[0] for r in results) / len(results)
        return float(min(avg_score, 1.0))


class ResumeOptimizer:
    """Generate resume improvements and optimizations."""
    
    def __init__(self, llm_analyzer):
        """Initialize optimizer."""
        self.llm_analyzer = llm_analyzer
    
    def generate_improvements(
        self,
        resume_text: str,
        job_description: str,
        gap_analysis: Dict
    ) -> Dict:
        """Generate personalized resume improvement suggestions."""
        
        prompt = self._build_improvement_prompt(
            resume_text,
            job_description,
            gap_analysis
        )
        
        response = self.llm_analyzer.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert resume writer and ATS specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
        
        suggestions = response.choices[0].message.content
        
        return {
            "ats_optimization": self._extract_section(suggestions, "ATS Optimization"),
            "content_improvements": self._extract_section(suggestions, "Content Improvements"),
            "formatting_tips": self._extract_section(suggestions, "Formatting Tips"),
            "action_items": self._extract_action_items(suggestions)
        }
    
    def rewrite_bullet_points(
        self,
        original_bullets: List[str],
        job_description: str = None
    ) -> Dict:
        """Rewrite bullet points with strong action verbs and quantified impact."""
        
        prompt = self._build_rewrite_prompt(original_bullets, job_description)
        
        response = self.llm_analyzer.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at writing powerful resume bullet points with quantified impact and strong action verbs."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
        
        rewritten = response.choices[0].message.content
        bullets = self._parse_bullet_points(rewritten)
        
        return {
            "original_count": len(original_bullets),
            "rewritten_bullets": bullets,
            "improvements": self._compare_bullets(original_bullets, bullets)
        }
    
    @staticmethod
    def _build_improvement_prompt(
        resume_text: str,
        job_description: str,
        gap_analysis: Dict
    ) -> str:
        """Build prompt for resume improvements."""
        
        # Extract skill names from critical gaps (which are dicts)
        critical_gaps = gap_analysis.get('critical_gaps', [])
        critical_gap_skills = [gap['skill'] for gap in critical_gaps[:3]]
        
        return f"""Analyze this resume and provide specific, actionable improvements:

CURRENT RESUME (excerpt):
{resume_text[:1500]}

TARGET JOB DESCRIPTION (excerpt):
{job_description[:1500]}

SKILL GAP ANALYSIS:
- Match Score: {gap_analysis.get('ats_score', 0)}/100
- Matched Skills: {', '.join(gap_analysis.get('matched_skills', []))}
- Critical Gaps: {', '.join(critical_gap_skills)}

Please provide:

ATS Optimization:
[specific changes to improve ATS parsing]

Content Improvements:
[suggestions to better highlight relevant skills]

Formatting Tips:
[formatting best practices]

Action Items:
[prioritized to-do list]"""
    
    @staticmethod
    def _build_rewrite_prompt(
        bullets: List[str],
        job_description: str = None
    ) -> str:
        """Build prompt for bullet point rewriting."""
        
        job_context = f"\nTarget Job: {job_description[:500]}" if job_description else ""
        
        return f"""Rewrite these resume bullet points to be more impactful using:
- Strong action verbs (not: worked, responsible for, involved in)
- Quantified metrics (numbers, percentages, improvements)
- Business impact (money saved, time reduced, efficiency improved)
- Technical specificity (tools, technologies, methodologies){job_context}

Original bullet points:
{chr(10).join(f'• {b}' for b in bullets)}

Rewritten bullet points (keep same structure, enhance impact):"""
    
    @staticmethod
    def _extract_section(text: str, section_name: str) -> str:
        """Extract specific section from response."""
        if section_name not in text:
            return ""
        
        start = text.find(section_name)
        end = text.find("\n\n", start)
        
        if end == -1:
            end = len(text)
        
        return text[start:end].strip()
    
    @staticmethod
    def _extract_action_items(text: str) -> List[str]:
        """Extract action items from suggestions."""
        lines = text.split("\n")
        items = [line.strip() for line in lines if line.strip().startswith("•") or line.strip().startswith("-")]
        return items[:5]
    
    @staticmethod
    def _parse_bullet_points(text: str) -> List[str]:
        """Parse rewritten bullet points."""
        lines = text.split("\n")
        bullets = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith("•") or line.startswith("-")):
                bullet = line.lstrip("•-").strip()
                if bullet:
                    bullets.append(bullet)
        
        return bullets
    
    @staticmethod
    def _compare_bullets(original: List[str], rewritten: List[str]) -> List[Dict]:
        """Compare original and rewritten bullets."""
        comparisons = []
        
        for orig, rewr in zip(original, rewritten):
            comparisons.append({
                "original": orig,
                "rewritten": rewr,
                "improvements": ResumeOptimizer._identify_improvements(orig, rewr)
            })
        
        return comparisons
    
    @staticmethod
    def _identify_improvements(original: str, rewritten: str) -> List[str]:
        """Identify what was improved."""
        improvements = []
        
        action_verbs = ["achieved", "increased", "improved", "optimized", "implemented", "developed"]
        if any(verb in rewritten.lower() for verb in action_verbs):
            improvements.append("Stronger action verb")
        
        import re
        if re.search(r'\d+%|\d+x|[$]\d+', rewritten):
            improvements.append("Added quantified metrics")
        
        if len(rewritten) > len(original):
            improvements.append("Added specific details")
        
        return improvements or ["Enhanced clarity"]
