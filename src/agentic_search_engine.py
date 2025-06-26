"""
Advanced AI Search Engine with Query Intelligence
Features: Query expansion, context awareness, intelligent ranking
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from pathlib import Path

@dataclass
class SearchContext:
    """Context information for search queries"""
    current_directory: Optional[str] = None
    recent_files: List[str] = None
    time_of_day: str = None
    day_of_week: str = None
    query_history: List[str] = None
    file_access_patterns: Dict[str, int] = None

@dataclass 
class SearchResult:
    """Enhanced search result with explanation"""
    file_path: str
    filename: str
    similarity_score: float
    relevance_explanation: str
    content_preview: str
    category: str
    last_modified: str
    file_size_mb: float
    why_relevant: List[str]
    confidence: float

class QueryExpander:
    """Expands queries with semantic variations and domain terms"""
    
    def __init__(self):
        # Domain-specific expansions
        self.domain_expansions = {
            'financial': ['revenue', 'profit', 'earnings', 'budget', 'cost', 'ROI', 'expenses', 'income'],
            'customer': ['client', 'user', 'consumer', 'satisfaction', 'feedback', 'support', 'service'],
            'technical': ['development', 'code', 'programming', 'software', 'system', 'implementation'],
            'business': ['strategy', 'planning', 'management', 'operations', 'performance', 'metrics'],
            'marketing': ['campaign', 'promotion', 'advertising', 'branding', 'engagement', 'conversion'],
            'project': ['task', 'milestone', 'deadline', 'deliverable', 'timeline', 'resource', 'scope'],
            'data': ['analysis', 'statistics', 'metrics', 'insights', 'trends', 'patterns', 'report'],
            'meeting': ['discussion', 'agenda', 'notes', 'minutes', 'action items', 'decision']
        }
        
        # Synonym mappings
        self.synonyms = {
            'error': ['bug', 'issue', 'problem', 'failure', 'exception'],
            'improve': ['enhance', 'optimize', 'better', 'upgrade', 'refine'],
            'urgent': ['critical', 'important', 'priority', 'immediate', 'asap'],
            'update': ['change', 'modify', 'revise', 'edit', 'refresh'],
            'plan': ['strategy', 'roadmap', 'schedule', 'timeline', 'blueprint']
        }
    
    def expand_query(self, query: str, max_expansions: int = 5) -> List[str]:
        """Generate semantic expansions of the query"""
        expansions = [query]  # Original query first
        query_lower = query.lower()
        words = re.findall(r'\b\w+\b', query_lower)
        
        # Add domain-specific terms
        for domain, terms in self.domain_expansions.items():
            if domain in query_lower or any(word in query_lower for word in terms[:3]):
                for term in terms[:2]:
                    if term not in query_lower:
                        expanded = f"{query} {term}"
                        expansions.append(expanded)
                        if len(expansions) >= max_expansions:
                            break
        
        # Add synonym variations
        for word in words:
            if word in self.synonyms:
                for synonym in self.synonyms[word][:2]:
                    expanded = query.replace(word, synonym)
                    expansions.append(expanded)
                    if len(expansions) >= max_expansions:
                        break
        
        # Add phrase variations
        if len(words) > 1:
            # Try partial phrases
            expansions.append(' '.join(words[:-1]))  # Remove last word
            expansions.append(' '.join(words[1:]))   # Remove first word
        
        return expansions[:max_expansions]

class IntentAnalyzer:
    """Analyzes user query intent and context"""
    
    def __init__(self):
        self.intent_patterns = {
            'find_recent': [
                r'\b(recent|latest|new|today|yesterday|this week)\b',
                r'\b(updated|modified|changed)\b'
            ],
            'find_specific': [
                r'\b(find|locate|where is|show me)\b',
                r'\b(specific|exact|particular)\b'
            ],
            'analyze_content': [
                r'\b(analyze|review|summarize|explain)\b',
                r'\b(what does|tell me about|information on)\b'
            ],
            'compare': [
                r'\b(compare|versus|vs|difference|similar)\b',
                r'\b(better|worse|best|worst)\b'
            ],
            'urgent': [
                r'\b(urgent|critical|important|asap|immediate)\b',
                r'\b(need now|quickly|fast)\b'
            ]
        }
    
    def analyze_intent(self, query: str, context: SearchContext = None) -> Dict:
        """Analyze query intent and extract key information"""
        query_lower = query.lower()
        
        # Detect intent patterns
        detected_intents = []
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    detected_intents.append(intent)
                    break
        
        # Extract time references
        time_refs = []
        time_patterns = {
            'today': r'\btoday\b',
            'yesterday': r'\byesterday\b', 
            'this_week': r'\bthis week\b',
            'last_week': r'\blast week\b',
            'this_month': r'\bthis month\b'
        }
        
        for time_name, pattern in time_patterns.items():
            if re.search(pattern, query_lower):
                time_refs.append(time_name)
        
        # Extract file type hints
        file_type_hints = []
        if re.search(r'\b(document|doc|pdf)\b', query_lower):
            file_type_hints.append('document')
        if re.search(r'\b(spreadsheet|excel|csv|data)\b', query_lower):
            file_type_hints.append('data')
        if re.search(r'\b(code|script|program)\b', query_lower):
            file_type_hints.append('code')
        
        # Extract key entities (simple NER)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        
        return {
            'intents': detected_intents,
            'time_references': time_refs,
            'file_type_hints': file_type_hints,
            'entities': entities,
            'is_urgent': 'urgent' in detected_intents,
            'needs_recent_files': bool(time_refs or 'find_recent' in detected_intents),
            'is_analytical': 'analyze_content' in detected_intents
        }

class SmartRanker:
    """Intelligent result ranking using multiple signals"""
    
    def __init__(self):
        self.ranking_weights = {
            'semantic_similarity': 0.4,
            'recency': 0.2,
            'file_type_match': 0.15,
            'filename_match': 0.15,
            'access_frequency': 0.1
        }
    
    def calculate_relevance_score(self, result: Dict, query: str, 
                                 intent_analysis: Dict, context: SearchContext) -> float:
        """Calculate comprehensive relevance score"""
        scores = {}
        
        # 1. Semantic similarity (from embedding)
        scores['semantic_similarity'] = result.get('similarity_score', 0.0)
        
        # 2. Recency bonus
        scores['recency'] = self._calculate_recency_score(result, intent_analysis)
        
        # 3. File type match
        scores['file_type_match'] = self._calculate_file_type_score(result, intent_analysis)
        
        # 4. Filename keyword match
        scores['filename_match'] = self._calculate_filename_score(result, query)
        
        # 5. Access frequency (if available)
        scores['access_frequency'] = self._calculate_access_score(result, context)
        
        # Weighted combination
        total_score = sum(
            scores[factor] * self.ranking_weights[factor]
            for factor in self.ranking_weights
        )
        
        return min(1.0, max(0.0, total_score))
    
    def _calculate_recency_score(self, result: Dict, intent_analysis: Dict) -> float:
        """Calculate recency-based score"""
        if not intent_analysis.get('needs_recent_files'):
            return 0.5  # Neutral if recency not important
        
        try:
            # Get last modified time
            modified_str = result.get('last_modified', result.get('metadata', {}).get('modified', ''))
            if not modified_str:
                return 0.0
            
            modified_time = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
            now = datetime.now()
            days_old = (now - modified_time).days
            
            # Scoring: 1.0 for today, 0.8 for yesterday, declining
            if days_old == 0:
                return 1.0
            elif days_old == 1:
                return 0.8
            elif days_old <= 7:
                return 0.6
            elif days_old <= 30:
                return 0.4
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_file_type_score(self, result: Dict, intent_analysis: Dict) -> float:
        """Calculate file type match score"""
        file_hints = intent_analysis.get('file_type_hints', [])
        if not file_hints:
            return 0.5  # Neutral if no type preference
        
        result_category = result.get('category', 'unknown').lower()
        
        for hint in file_hints:
            if hint == 'document' and result_category in ['document', 'text']:
                return 1.0
            elif hint == 'data' and result_category == 'data':
                return 1.0
            elif hint == 'code' and result_category == 'code':
                return 1.0
        
        return 0.3  # Lower score if type doesn't match
    
    def _calculate_filename_score(self, result: Dict, query: str) -> float:
        """Calculate filename keyword match score"""
        filename = result.get('filename', '').lower()
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        if not query_words:
            return 0.0
        
        # Check for exact word matches in filename
        filename_words = set(re.findall(r'\b\w+\b', filename))
        matches = query_words.intersection(filename_words)
        
        if matches:
            return len(matches) / len(query_words)
        
        # Check for partial matches
        partial_score = 0
        for word in query_words:
            if word in filename:
                partial_score += 0.5
        
        return min(1.0, partial_score / len(query_words))
    
    def _calculate_access_score(self, result: Dict, context: SearchContext) -> float:
        """Calculate access frequency score"""
        if not context or not context.file_access_patterns:
            return 0.5
        
        file_path = result.get('file_path', '')
        access_count = context.file_access_patterns.get(file_path, 0)
        
        if access_count == 0:
            return 0.3
        elif access_count <= 2:
            return 0.6
        elif access_count <= 5:
            return 0.8
        else:
            return 1.0

class ExplanationGenerator:
    """Generates human-readable explanations for search results"""
    
    def __init__(self):
        self.explanation_templates = {
            'high_similarity': "This document closely matches your query about '{query}'",
            'recent_file': "This is a recently modified file from {date}",
            'filename_match': "The filename contains keywords from your search: {keywords}",
            'category_match': "This {category} file matches your search for {type} content",
            'frequent_access': "This is a frequently accessed file in your workflow"
        }
    
    def generate_explanation(self, result: Dict, query: str, 
                           intent_analysis: Dict, score_breakdown: Dict) -> str:
        """Generate explanation for why this result is relevant"""
        explanations = []
        
        # High similarity explanation
        similarity = result.get('similarity_score', 0)
        if similarity > 0.7:
            explanations.append(
                self.explanation_templates['high_similarity'].format(query=query)
            )
        
        # Recency explanation
        if intent_analysis.get('needs_recent_files') and score_breakdown.get('recency', 0) > 0.7:
            try:
                modified_str = result.get('last_modified', '')
                if modified_str:
                    date = datetime.fromisoformat(modified_str.replace('Z', '+00:00')).strftime('%B %d, %Y')
                    explanations.append(
                        self.explanation_templates['recent_file'].format(date=date)
                    )
            except:
                pass
        
        # Filename match explanation
        filename_score = score_breakdown.get('filename_match', 0)
        if filename_score > 0.5:
            filename = result.get('filename', '')
            query_words = re.findall(r'\b\w+\b', query.lower())
            matched_words = [word for word in query_words if word in filename.lower()]
            if matched_words:
                explanations.append(
                    self.explanation_templates['filename_match'].format(
                        keywords=', '.join(matched_words)
                    )
                )
        
        # Category match explanation
        file_hints = intent_analysis.get('file_type_hints', [])
        category = result.get('category', '')
        if file_hints and category:
            for hint in file_hints:
                if ((hint == 'document' and category in ['document', 'text']) or
                    (hint == 'data' and category == 'data') or
                    (hint == 'code' and category == 'code')):
                    explanations.append(
                        self.explanation_templates['category_match'].format(
                            category=category, type=hint
                        )
                    )
                    break
        
        # Default explanation if none of the above
        if not explanations:
            explanations.append(f"Contains relevant content related to '{query}'")
        
        return '. '.join(explanations) + '.'

class AgenticSearchEngine:
    """Main search engine with AI-powered query understanding and ranking"""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.query_expander = QueryExpander()
        self.intent_analyzer = IntentAnalyzer()
        self.ranker = SmartRanker()
        self.explanation_generator = ExplanationGenerator()
        
        # Search history and context
        self.search_history = []
        self.file_access_patterns = {}
        
        print("🤖 Agentic Search Engine ready!")
    
    def update_file_access(self, file_path: str):
        """Track file access for ranking"""
        self.file_access_patterns[file_path] = self.file_access_patterns.get(file_path, 0) + 1
    
    def get_search_context(self, current_dir: str = None) -> SearchContext:
        """Build search context from current state"""
        return SearchContext(
            current_directory=current_dir,
            recent_files=list(self.file_access_patterns.keys())[-10:],
            time_of_day=datetime.now().strftime('%H:%M'),
            day_of_week=datetime.now().strftime('%A'),
            query_history=self.search_history[-5:],
            file_access_patterns=self.file_access_patterns.copy()
        )
    
    def search(self, query: str, top_k: int = 10, current_dir: str = None) -> List[SearchResult]:
        """Perform intelligent search with context awareness"""
        
        print(f"🔍 Agentic search for: '{query}'")
        
        # Build context
        context = self.get_search_context(current_dir)
        
        # Analyze query intent
        intent_analysis = self.intent_analyzer.analyze_intent(query, context)
        print(f"   🎯 Detected intents: {intent_analysis['intents']}")
        
        # Expand query if beneficial
        expanded_queries = self.query_expander.expand_query(query)
        print(f"   📝 Query expansions: {len(expanded_queries)}")
        
        # Perform searches with all query variations
        all_results = {}  # file_path -> best_result
        
        for expanded_query in expanded_queries:
            raw_results = self.indexer.search(expanded_query, top_k * 2)
            
            for result in raw_results:
                file_path = result['file_path']
                
                # Keep best score for each file
                if (file_path not in all_results or 
                    result['similarity_score'] > all_results[file_path]['similarity_score']):
                    all_results[file_path] = result
        
        # Re-rank results using intelligent ranking
        enhanced_results = []
        
        for result in all_results.values():
            # Calculate comprehensive relevance score
            score_breakdown = {}
            
            # Get individual scoring components
            score_breakdown['semantic_similarity'] = result.get('similarity_score', 0.0)
            score_breakdown['recency'] = self.ranker._calculate_recency_score(result, intent_analysis)
            score_breakdown['file_type_match'] = self.ranker._calculate_file_type_score(result, intent_analysis)
            score_breakdown['filename_match'] = self.ranker._calculate_filename_score(result, query)
            score_breakdown['access_frequency'] = self.ranker._calculate_access_score(result, context)
            
            # Calculate final relevance score
            relevance_score = self.ranker.calculate_relevance_score(
                result, query, intent_analysis, context
            )
            
            # Generate explanation
            explanation = self.explanation_generator.generate_explanation(
                result, query, intent_analysis, score_breakdown
            )
            
            # Create enhanced result
            enhanced_result = SearchResult(
                file_path=result['file_path'],
                filename=result['filename'],
                similarity_score=result['similarity_score'],
                relevance_explanation=explanation,
                content_preview=result.get('content', '')[:300] + '...',
                category=result.get('category', 'unknown'),
                last_modified=result.get('metadata', {}).get('modified', 'unknown'),
                file_size_mb=result.get('metadata', {}).get('size_mb', 0),
                why_relevant=[explanation],
                confidence=relevance_score
            )
            
            enhanced_results.append(enhanced_result)
        
        # Sort by relevance score
        enhanced_results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Track search in history
        self.search_history.append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results_count': len(enhanced_results),
            'intent': intent_analysis
        })
        
        # Return top results
        final_results = enhanced_results[:top_k]
        
        print(f"   ✅ Returning {len(final_results)} intelligently ranked results")
        
        return final_results
    
    def suggest_files(self, context_hint: str = None) -> List[SearchResult]:
        """Proactively suggest relevant files based on context"""
        suggestions = []
        
        # Get current context
        context = self.get_search_context()
        
        # Time-based suggestions
        current_hour = datetime.now().hour
        
        if 9 <= current_hour <= 17:  # Business hours
            # Suggest frequently accessed work files
            work_queries = ["meeting", "report", "project", "status"]
        else:
            # Suggest personal or learning files
            work_queries = ["notes", "ideas", "learning", "personal"]
        
        # Recent file suggestions
        if context.recent_files:
            recent_query = "recent documents"
            recent_results = self.search(recent_query, top_k=3)
            suggestions.extend(recent_results[:2])
        
        # Context-based suggestions
        if context_hint:
            context_results = self.search(context_hint, top_k=3)
            suggestions.extend(context_results[:2])
        
        return suggestions[:5]
    
    def get_search_analytics(self) -> Dict:
        """Get analytics about search patterns"""
        if not self.search_history:
            return {"message": "No search history available"}
        
        # Analyze search patterns
        total_searches = len(self.search_history)
        recent_searches = [s for s in self.search_history 
                          if (datetime.now() - datetime.fromisoformat(s['timestamp'])).days <= 7]
        
        # Most common intents
        intent_counts = {}
        for search in self.search_history:
            for intent in search.get('intent', {}).get('intents', []):
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Most accessed files
        top_files = sorted(self.file_access_patterns.items(), 
                          key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_searches': total_searches,
            'searches_last_7_days': len(recent_searches),
            'avg_results_per_search': sum(s['results_count'] for s in self.search_history) / total_searches,
            'most_common_intents': intent_counts,
            'most_accessed_files': [{'file': f[0], 'access_count': f[1]} for f in top_files]
        }

# Test the agentic search engine
if __name__ == "__main__":
    from incremental_indexer import IncrementalIndexer
    from document_extractor import EnhancedDocumentExtractor
    from filesystem_scanner import FilesystemScanner, ScanConfig
    
    print("🧪 Testing Agentic Search Engine...")
    
    # Create components
    indexer = IncrementalIndexer()
    extractor = EnhancedDocumentExtractor()
    search_engine = AgenticSearchEngine(indexer)
    
    # Quick index if needed
    if not indexer.documents:
        print("📚 Building test index...")
        config = ScanConfig(include_dirs=["../data/documents"], max_file_size_mb=5)
        scanner = FilesystemScanner(config)
        files = scanner.scan_system()
        indexer.incremental_index(files, extractor, max_workers=2)
    
    # Test searches with different intents
    test_queries = [
        "financial performance",  # Basic search
        "recent customer feedback",  # Time-based search
        "find project meeting notes",  # Specific search
        "urgent budget analysis",  # Urgent search
        "compare revenue data"  # Analytical search
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        results = search_engine.search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.filename}")
            print(f"      📊 Confidence: {result.confidence:.3f}")
            print(f"      💭 Why: {result.relevance_explanation}")
    
    # Test file suggestions
    print(f"\n💡 File suggestions:")
    suggestions = search_engine.suggest_files("work meeting")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion.filename} (confidence: {suggestion.confidence:.3f})")
    
    # Show analytics
    analytics = search_engine.get_search_analytics()
    print(f"\n📈 Search Analytics:")
    for key, value in analytics.items():
        print(f"   {key}: {value}")