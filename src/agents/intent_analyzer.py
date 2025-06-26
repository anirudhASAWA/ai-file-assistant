"""
Intent Analyzer - The Brain of Agentic Search
Understands what users really want when they search
"""

import re
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import dateparser

@dataclass
class SearchIntent:
    """Structured representation of user's search intent"""
    query_type: str  # "find", "show", "help", "organize", etc.
    target_objects: List[str]  # ["documents", "images", "code"]
    time_context: Optional[Dict[str, Any]]  # Date ranges, recency
    domain_context: str  # "work", "personal", "technical", "financial"
    urgency: str  # "high", "medium", "low"
    task_context: str  # "presentation", "meeting", "analysis", etc.
    file_attributes: Dict[str, Any]  # Size, type, location preferences
    relationships: List[str]  # Related people, projects, topics

class IntentAnalyzer:
    """Analyzes user queries to understand true intent"""
    
    def __init__(self):
        # Time-related patterns
        self.time_patterns = {
            'recent': ['recent', 'latest', 'new', 'fresh'],
            'specific_date': ['yesterday', 'last week', 'last month', 'last year'],
            'seasonal': ['quarterly', 'annual', 'monthly', 'weekly'],
            'relative': ['before', 'after', 'since', 'until', 'between']
        }
        
        # Domain indicators
        self.domain_patterns = {
            'financial': ['sales', 'revenue', 'profit', 'budget', 'tax', 'financial', 'quarterly', 'earnings'],
            'technical': ['code', 'script', 'function', 'api', 'database', 'algorithm', 'debug'],
            'personal': ['photos', 'family', 'vacation', 'personal', 'diary', 'journal'],
            'work': ['meeting', 'project', 'team', 'client', 'presentation', 'report', 'deadline'],
            'creative': ['design', 'image', 'video', 'music', 'art', 'creative', 'draft']
        }
        
        # Task context patterns
        self.task_patterns = {
            'presentation': ['presentation', 'slides', 'deck', 'meeting', 'pitch'],
            'analysis': ['analyze', 'analysis', 'data', 'trends', 'metrics', 'performance'],
            'reference': ['find', 'lookup', 'reference', 'check', 'verify'],
            'organization': ['organize', 'clean', 'sort', 'categorize', 'manage']
        }
        
        # Urgency indicators
        self.urgency_patterns = {
            'high': ['urgent', 'asap', 'immediately', 'now', 'emergency', 'critical'],
            'medium': ['soon', 'today', 'tomorrow', 'this week'],
            'low': ['whenever', 'eventually', 'no rush', 'sometime']
        }
    
    def analyze_intent(self, user_query: str) -> SearchIntent:
        """Main method to analyze user's intent"""
        query = user_query.lower().strip()
        
        # Determine query type
        query_type = self._identify_query_type(query)
        
        # Extract target objects
        target_objects = self._extract_target_objects(query)
        
        # Analyze time context
        time_context = self._analyze_time_context(query)
        
        # Determine domain
        domain_context = self._identify_domain(query)
        
        # Assess urgency
        urgency = self._assess_urgency(query)
        
        # Identify task context
        task_context = self._identify_task_context(query)
        
        # Extract file attributes
        file_attributes = self._extract_file_attributes(query)
        
        # Find relationships
        relationships = self._extract_relationships(query)
        
        return SearchIntent(
            query_type=query_type,
            target_objects=target_objects,
            time_context=time_context,
            domain_context=domain_context,
            urgency=urgency,
            task_context=task_context,
            file_attributes=file_attributes,
            relationships=relationships
        )
    
    def _identify_query_type(self, query: str) -> str:
        """Identify the type of query"""
        if any(word in query for word in ['find', 'search', 'locate', 'look for']):
            return 'find'
        elif any(word in query for word in ['show', 'display', 'list', 'see']):
            return 'show'
        elif any(word in query for word in ['help', 'how', 'what is', 'explain']):
            return 'help'
        elif any(word in query for word in ['organize', 'sort', 'clean', 'manage']):
            return 'organize'
        else:
            return 'find'  # Default
    
    def _extract_target_objects(self, query: str) -> List[str]:
        """Extract what the user is looking for"""
        objects = []
        
        # File types
        file_types = {
            'documents': ['document', 'doc', 'pdf', 'file', 'paper', 'report'],
            'images': ['image', 'photo', 'picture', 'screenshot', 'pic'],
            'spreadsheets': ['spreadsheet', 'excel', 'csv', 'data', 'sheet'],
            'presentations': ['presentation', 'slides', 'deck', 'powerpoint'],
            'code': ['code', 'script', 'function', 'program', 'source'],
            'emails': ['email', 'mail', 'message', 'correspondence'],
            'videos': ['video', 'movie', 'clip', 'recording'],
            'audio': ['audio', 'music', 'sound', 'recording', 'podcast']
        }
        
        for obj_type, keywords in file_types.items():
            if any(keyword in query for keyword in keywords):
                objects.append(obj_type)
        
        return objects if objects else ['files']  # Default to general files
    
    def _analyze_time_context(self, query: str) -> Optional[Dict[str, Any]]:
        """Analyze temporal aspects of the query"""
        time_context = {}
        
        # Look for specific dates
        date_matches = re.findall(r'\b\d{4}\b', query)  # Years
        if date_matches:
            time_context['years'] = date_matches
        
        # Parse relative dates
        relative_dates = []
        for pattern_type, keywords in self.time_patterns.items():
            for keyword in keywords:
                if keyword in query:
                    relative_dates.append(keyword)
        
        if relative_dates:
            time_context['relative'] = relative_dates
            
            # Try to parse into actual dates
            for rel_date in relative_dates:
                parsed = dateparser.parse(rel_date)
                if parsed:
                    time_context['parsed_dates'] = time_context.get('parsed_dates', [])
                    time_context['parsed_dates'].append(parsed)
        
        return time_context if time_context else None
    
    def _identify_domain(self, query: str) -> str:
        """Identify the domain/context of the search"""
        domain_scores = {}
        
        for domain, keywords in self.domain_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return 'general'
    
    def _assess_urgency(self, query: str) -> str:
        """Determine urgency level"""
        for urgency_level, keywords in self.urgency_patterns.items():
            if any(keyword in query for keyword in keywords):
                return urgency_level
        
        return 'medium'  # Default
    
    def _identify_task_context(self, query: str) -> str:
        """Identify the task context"""
        for task, keywords in self.task_patterns.items():
            if any(keyword in query for keyword in keywords):
                return task
        
        return 'reference'  # Default
    
    def _extract_file_attributes(self, query: str) -> Dict[str, Any]:
        """Extract preferences about file attributes"""
        attributes = {}
        
        # Size preferences
        if any(word in query for word in ['large', 'big', 'huge']):
            attributes['size_preference'] = 'large'
        elif any(word in query for word in ['small', 'tiny', 'compact']):
            attributes['size_preference'] = 'small'
        
        # Location preferences
        if 'desktop' in query:
            attributes['location_preference'] = 'desktop'
        elif 'documents' in query:
            attributes['location_preference'] = 'documents'
        elif 'downloads' in query:
            attributes['location_preference'] = 'downloads'
        
        return attributes
    
    def _extract_relationships(self, query: str) -> List[str]:
        """Extract relationships (people, projects, topics)"""
        relationships = []
        
        # Look for project names (capitalized words)
        project_matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        relationships.extend(project_matches)
        
        # Look for common relationship indicators
        if 'project' in query:
            relationships.append('project-related')
        if 'team' in query:
            relationships.append('team-related')
        if 'client' in query:
            relationships.append('client-related')
        
        return relationships

# Test the intent analyzer
if __name__ == "__main__":
    analyzer = IntentAnalyzer()
    
    test_queries = [
        "Find quarterly sales reports from last year",
        "Show me the code I wrote for authentication last month",
        "I need photos from my vacation in 2023",
        "Help me find the presentation for tomorrow's meeting",
        "Where are my tax documents?"
    ]
    
    for query in test_queries:
        intent = analyzer.analyze_intent(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {intent}")
