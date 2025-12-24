"""Core NLP processing pipeline for resume analysis."""
import re
from typing import List, Dict, Tuple
import spacy
from spacy.tokens import Doc
from config import settings


class ResumePipeline:
    """Production-grade resume processing pipeline."""
    
    def __init__(self):
        """Initialize spaCy model and preprocessing patterns."""
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            print(f"Downloading {settings.SPACY_MODEL}...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", settings.SPACY_MODEL])
            self.nlp = spacy.load(settings.SPACY_MODEL)
        
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        self.url_pattern = r'https?://(?:www\.)?[\w\-\.]+\.\w+'
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """Extract email, phone, and URLs from resume."""
        return {
            "emails": re.findall(self.email_pattern, text),
            "phones": re.findall(self.phone_pattern, text),
            "urls": re.findall(self.url_pattern, text),
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """Extract named entities using spaCy."""
        doc = self.nlp(text)
        
        entities_dict = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "other": []
        }
        
        for ent in doc.ents:
            entity_info = {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            
            if ent.label_ == "PERSON":
                entities_dict["persons"].append(entity_info)
            elif ent.label_ == "ORG":
                entities_dict["organizations"].append(entity_info)
            elif ent.label_ == "GPE":
                entities_dict["locations"].append(entity_info)
            else:
                entities_dict["other"].append(entity_info)
        
        return entities_dict
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume."""
        text_lower = text.lower()
        
        # Predefined skill keywords (including multi-word skills)
        common_skills = {
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'nodejs', 'node.js', 'express', 'django', 'flask', 'fastapi', 'sql', 'nosql',
            'mongodb', 'postgresql', 'mysql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'ci/cd', 'machine learning', 'nlp', 'deep learning', 'tensorflow',
            'pytorch', 'scikit-learn', 'sklearn', 'pandas', 'numpy', 'api', 'rest', 'graphql',
            'html', 'css', 'scss', 'sass', 'webpack', 'babel', 'linux', 'windows',
            'c++', 'c#', 'golang', 'go', 'rust', 'ruby', 'php', 'kotlin', 'swift',
            'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'jenkins', 'gitlab', 'github',
            'terraform', 'ansible', 'jira', 'confluence', 'agile', 'scrum', 'devops',
            'microservices', 'restful', 'api design', 'system design', 'data structures',
            'algorithms', 'oop', 'functional programming', 'tdd', 'testing',
            'unit testing', 'integration testing', 'pytest', 'jest', 'mocha',
            'backend', 'frontend', 'full stack', 'fullstack', 'full-stack',
            'react native', 'flutter', 'android', 'ios', 'mobile development',
            'web development', 'software development', 'data science', 'data analysis',
            'data engineering', 'etl', 'bi', 'tableau', 'power bi', 'spark', 'hadoop',
            'jupyter', 'r programming', 'matlab', 'excel', 'vba',
        }
        
        found_skills = []
        
        # Check for multi-word skills first (longer matches first)
        sorted_skills = sorted(common_skills, key=len, reverse=True)
        
        for skill in sorted_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks for embedding."""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end].strip())
            start += (chunk_size - overlap)
        
        return [chunk for chunk in chunks if len(chunk) > 10]
    
    def get_key_sections(self, text: str) -> Dict[str, str]:
        """Extract and identify key resume sections."""
        text_lower = text.lower()
        
        section_patterns = {
            "summary": r'(?:professional\s+)?summary|objective',
            "experience": r'(?:work\s+)?experience|employment history',
            "education": r'education|academic|degree',
            "skills": r'skills|competencies|technical skills',
            "certifications": r'certifications?|licenses?|achievements?',
            "projects": r'projects?|portfolio',
        }
        
        sections = {}
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                start_pos = match.start()
                # Find next section start
                next_section_pos = len(text)
                for other_pattern in section_patterns.values():
                    if other_pattern != pattern:
                        other_match = re.search(other_pattern, text_lower[start_pos+10:])
                        if other_match:
                            next_section_pos = min(next_section_pos, start_pos + 10 + other_match.start())
                
                sections[section_name] = text[start_pos:next_section_pos].strip()
        
        return sections
    
    def process_resume(self, text: str) -> Dict:
        """Complete resume processing pipeline."""
        cleaned_text = self._clean_text(text)
        
        return {
            "raw_text": cleaned_text,
            "contact_info": self.extract_contact_info(cleaned_text),
            "entities": self.extract_entities(cleaned_text),
            "skills": self.extract_skills(cleaned_text),
            "sections": self.get_key_sections(cleaned_text),
            "chunks": self.chunk_text(cleaned_text),
            "token_count": len(cleaned_text.split()),
        }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize resume text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s@.\-+()/#&,]', '', text)
        return text.strip()
