"""
Advanced ATS scoring and skill gap analysis system.
Production-grade scoring logic with weighted skill matching.
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class SkillCategory(Enum):
    """Skill importance categories for scoring."""
    CRITICAL = 3.0      # Must-have
    IMPORTANT = 2.0     # Highly desired
    NICE_TO_HAVE = 1.0  # Bonus


@dataclass
class SkillGap:
    """Represents a single skill gap."""
    skill: str
    category: str
    priority: float
    frequency_in_job: int
    alternative_skills: List[str]


@dataclass
class ATSScore:
    """Complete ATS scoring breakdown."""
    total_score: int
    skill_match_score: int
    experience_match_score: int
    keyword_match_score: int
    formatting_score: int
    breakdown: Dict[str, int]
    matched_skills: List[str]
    missing_skills: List[SkillGap]
    match_percentage: float


class ATSScoringEngine:
    """Production-grade ATS scoring system."""
    
    def __init__(self):
        """Initialize scoring weights and thresholds."""
        self.weights = {
            "skill_match": 0.40,      # 40% of score
            "experience": 0.25,        # 25% of score
            "keywords": 0.20,          # 20% of score
            "formatting": 0.15,        # 15% of score
        }
        
        self.critical_skill_multiplier = 1.5
        self.experience_years_weight = 5  # Points per year
        self.max_score = 100
    
    def calculate_ats_score(
        self,
        resume_data: Dict,
        job_description: str,
        job_requirements: Dict = None
    ) -> ATSScore:
        """Calculate comprehensive ATS score."""
        
        # Extract skills and keywords
        resume_skills = set(resume_data.get("skills", []))
        job_skills = self._extract_job_skills(job_description)
        job_keywords = self._extract_keywords(job_description)
        resume_keywords = self._extract_keywords(resume_data.get("raw_text", ""))
        
        # Calculate component scores
        skill_score = self._calculate_skill_score(resume_skills, job_skills)
        exp_score = self._calculate_experience_score(resume_data)
        keyword_score = self._calculate_keyword_score(resume_keywords, job_keywords)
        format_score = self._calculate_formatting_score(resume_data)
        
        # Calculate weighted total
        total = (
            skill_score * self.weights["skill_match"] +
            exp_score * self.weights["experience"] +
            keyword_score * self.weights["keywords"] +
            format_score * self.weights["formatting"]
        )
        
        # Calculate matched and missing skills
        matched = list(resume_skills & set(job_skills.keys()))
        missing = self._calculate_skill_gaps(
            resume_skills,
            job_skills,
            job_description,
            job_requirements
        )
        
        # Match percentage
        match_pct = (len(matched) / len(job_skills)) * 100 if job_skills else 0
        
        return ATSScore(
            total_score=int(total),
            skill_match_score=int(skill_score),
            experience_match_score=int(exp_score),
            keyword_match_score=int(keyword_score),
            formatting_score=int(format_score),
            breakdown={
                "skills": int(skill_score),
                "experience": int(exp_score),
                "keywords": int(keyword_score),
                "formatting": int(format_score),
            },
            matched_skills=sorted(matched),
            missing_skills=sorted(missing, key=lambda x: x.priority, reverse=True),
            match_percentage=min(match_pct, 100)
        )
    
    def _calculate_skill_score(self, resume_skills: set, job_skills: Dict) -> float:
        """Calculate skill match score (0-100)."""
        if not job_skills:
            return 100.0
        
        total_weight = 0
        matched_weight = 0
        
        for skill, weight in job_skills.items():
            total_weight += weight
            if skill.lower() in [s.lower() for s in resume_skills]:
                matched_weight += weight
        
        return (matched_weight / total_weight * 100) if total_weight > 0 else 0.0
    
    def _calculate_experience_score(self, resume_data: Dict) -> float:
        """Calculate experience relevance score (0-100)."""
        experience = resume_data.get("token_count", 0)
        
        # Normalize experience (assumes tokens correlate with content depth)
        exp_score = min((experience / 1000) * 100, 100)
        
        return exp_score
    
    def _calculate_keyword_score(self, resume_keywords: set, job_keywords: set) -> float:
        """Calculate keyword presence score (0-100)."""
        if not job_keywords:
            return 100.0
        
        matched = resume_keywords & job_keywords
        return (len(matched) / len(job_keywords)) * 100 if job_keywords else 0.0
    
    def _calculate_formatting_score(self, resume_data: Dict) -> float:
        """Calculate formatting and structure score (0-100)."""
        score = 100.0
        
        # Check for required sections
        required_sections = {"experience", "education", "skills"}
        found_sections = set(resume_data.get("sections", {}).keys())
        
        missing_sections = required_sections - found_sections
        score -= len(missing_sections) * 20
        
        # Check for contact info
        contact = resume_data.get("contact_info", {})
        if not contact.get("emails"):
            score -= 10
        if not contact.get("phones"):
            score -= 5
        
        return max(score, 0.0)
    
    def _calculate_skill_gaps(
        self,
        resume_skills: set,
        job_skills: Dict,
        job_description: str,
        requirements: Dict = None
    ) -> List[SkillGap]:
        """Identify and rank skill gaps."""
        gaps = []
        resume_lower = {s.lower() for s in resume_skills}
        
        for skill, weight in job_skills.items():
            if skill.lower() not in resume_lower:
                # Determine skill category
                if weight >= 2.5:
                    category = SkillCategory.CRITICAL.name
                elif weight >= 1.5:
                    category = SkillCategory.IMPORTANT.name
                else:
                    category = SkillCategory.NICE_TO_HAVE.name
                
                # Count frequency in job description
                frequency = job_description.lower().count(skill.lower())
                
                # Find alternative/related skills
                alternatives = self._find_alternative_skills(skill, resume_skills)
                
                gaps.append(SkillGap(
                    skill=skill,
                    category=category,
                    priority=weight,
                    frequency_in_job=frequency,
                    alternative_skills=alternatives
                ))
        
        return gaps
    
    @staticmethod
    def _extract_job_skills(job_description: str) -> Dict[str, float]:
        """Extract skills from job description with weights."""
        common_skills = {
            # Programming Languages (Critical)
            'python': 3.0, 'java': 3.0, 'javascript': 2.5, 'typescript': 2.5,
            'c++': 2.5, 'c#': 2.5, 'golang': 2.5, 'go': 2.5, 'rust': 2.5,
            'ruby': 2.0, 'php': 2.0, 'kotlin': 2.5, 'swift': 2.5,
            
            # Databases
            'sql': 2.5, 'nosql': 2.0, 'mongodb': 2.0, 'postgresql': 2.0, 
            'mysql': 2.0, 'redis': 2.0, 'elasticsearch': 2.0, 'oracle': 2.0,
            
            # Cloud & DevOps
            'aws': 2.5, 'azure': 2.5, 'gcp': 2.0, 'docker': 2.0, 
            'kubernetes': 2.0, 'ci/cd': 2.0, 'jenkins': 1.5, 'terraform': 2.0,
            'ansible': 1.5, 'gitlab': 1.5, 'github': 1.5,
            
            # Frontend
            'react': 2.5, 'angular': 2.0, 'vue': 2.0, 'node': 2.0, 'nodejs': 2.0,
            'html': 2.0, 'css': 2.0, 'sass': 1.5, 'webpack': 1.5,
            'react native': 2.5, 'flutter': 2.5,
            
            # Backend/APIs
            'django': 2.0, 'flask': 2.0, 'fastapi': 2.0, 'express': 2.0,
            'api': 2.0, 'rest': 2.0, 'restful': 2.0, 'graphql': 1.5,
            'microservices': 2.5, 'api design': 2.5,
            
            # Data Science & ML
            'machine learning': 3.0, 'deep learning': 3.0, 'nlp': 2.5,
            'tensorflow': 2.5, 'pytorch': 2.5, 'keras': 2.0,
            'pandas': 2.5, 'numpy': 2.5, 'scikit-learn': 2.5, 'sklearn': 2.5,
            'data science': 3.0, 'data analysis': 2.5, 'data engineering': 2.5,
            'spark': 2.5, 'hadoop': 2.0, 'etl': 2.0, 'tableau': 2.0, 'power bi': 2.0,
            
            # Testing & Quality
            'testing': 1.5, 'unit testing': 1.5, 'integration testing': 1.5,
            'tdd': 1.5, 'pytest': 1.5, 'jest': 1.5, 'mocha': 1.5,
            
            # Methodologies & Tools
            'git': 2.0, 'linux': 1.5, 'agile': 1.5, 'scrum': 1.5, 'devops': 2.0,
            'jira': 1.0, 'confluence': 1.0,
            
            # Soft Skills
            'leadership': 1.5, 'communication': 1.0, 'teamwork': 1.0,
            
            # Development Areas
            'backend': 2.0, 'frontend': 2.0, 'full stack': 2.5, 'fullstack': 2.5,
            'full-stack': 2.5, 'mobile development': 2.5, 'web development': 2.0,
            'software development': 2.0,
        }
        
        job_lower = job_description.lower()
        found_skills = {}
        
        # Sort by length to match longer phrases first
        sorted_skills = sorted(common_skills.items(), key=lambda x: len(x[0]), reverse=True)
        
        for skill, weight in sorted_skills:
            if skill in job_lower:
                found_skills[skill] = weight
        
        return found_skills
    
    @staticmethod
    def _extract_keywords(text: str) -> set:
        """Extract key technical keywords."""
        keywords = {
            'api', 'rest', 'graphql', 'sql', 'nosql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'ci/cd', 'agile', 'scrum', 'devops',
            'microservices', 'distributed', 'scalable',
            'responsive', 'optimization', 'performance',
            'security', 'authentication', 'database',
        }
        
        text_lower = text.lower()
        found = {kw for kw in keywords if kw in text_lower}
        return found
    
    @staticmethod
    def _find_alternative_skills(skill: str, resume_skills: set) -> List[str]:
        """Find alternative/related skills in resume."""
        # Skill relationships mapping
        skill_families = {
            'python': ['golang', 'ruby', 'javascript'],
            'java': ['kotlin', 'scala', 'c++'],
            'aws': ['azure', 'gcp', 'kubernetes'],
            'react': ['angular', 'vue', 'svelte'],
            'tensorflow': ['pytorch', 'keras'],
            'sql': ['postgresql', 'mysql', 'oracle'],
            'docker': ['podman', 'kubernetes'],
            'machine learning': ['deep learning', 'ai', 'nlp'],
        }
        
        skill_lower = skill.lower()
        related = skill_families.get(skill_lower, [])
        
        alternatives = []
        for related_skill in related:
            if any(related_skill.lower() in s.lower() for s in resume_skills):
                alternatives.append(related_skill)
        
        return alternatives


class SkillGapAnalyzer:
    """Advanced skill gap analysis with recommendations."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.ats_engine = ATSScoringEngine()
    
    def analyze_gaps(
        self,
        resume_data: Dict,
        job_description: str
    ) -> Dict:
        """Perform comprehensive gap analysis."""
        
        ats_score = self.ats_engine.calculate_ats_score(
            resume_data,
            job_description
        )
        
        return {
            "ats_score": ats_score.total_score,
            "match_percentage": ats_score.match_percentage,
            "matched_skills": ats_score.matched_skills,
            "missing_skills_count": len(ats_score.missing_skills),
            "critical_gaps": [
                {
                    "skill": gap.skill,
                    "priority": gap.priority,
                    "category": gap.category,
                    "alternatives": gap.alternative_skills,
                    "frequency": gap.frequency_in_job,
                    "recommendation": self._get_recommendation(gap)
                }
                for gap in ats_score.missing_skills[:5]  # Top 5 gaps
            ],
            "skill_breakdown": ats_score.breakdown,
            "improvement_priority": self._rank_improvements(ats_score.missing_skills)
        }
    
    @staticmethod
    def _get_recommendation(gap: SkillGap) -> str:
        """Generate recommendation for skill gap."""
        if gap.category == SkillCategory.CRITICAL.name:
            return f"CRITICAL: Learn {gap.skill} immediately - appears {gap.frequency_in_job}x in job description"
        elif gap.category == SkillCategory.IMPORTANT.name:
            return f"IMPORTANT: Acquire {gap.skill} to strengthen candidacy"
        else:
            return f"NICE-TO-HAVE: {gap.skill} would make you more competitive"
    
    @staticmethod
    def _rank_improvements(gaps: List[SkillGap]) -> List[str]:
        """Rank improvements by impact."""
        if not gaps:
            return []
        
        # Sort by priority and frequency
        sorted_gaps = sorted(
            gaps,
            key=lambda x: (x.priority, x.frequency_in_job),
            reverse=True
        )
        
        return [gap.skill for gap in sorted_gaps[:3]]
