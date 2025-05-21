import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import nltk
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class ClauseExtractor:
    """Rule-based clause extractor for contract analysis."""
    
    def __init__(self, config_path: str = "clause_definitions.json", log_level: int = logging.INFO):
        """
        Initialize the ClauseExtractor with clause definitions.
        
        Args:
            config_path: Path to the clause definitions JSON file
            log_level: Logging level for debug information
        """
        self.logger = self._setup_logging(log_level)
        self.config_path = Path(config_path)
        self.clause_definitions: Dict = {}
        self.global_config: Dict = {}
        self.compiled_patterns: Dict = {}
        
        # Initialize NLTK if available
        self._initialize_nltk()
        
        # Load configuration and set up preprocessing
        self._load_clause_definitions()
        self._setup_preprocessing()
        
    def _initialize_nltk(self) -> None:
        """Initialize NLTK resources if available."""
        if NLTK_AVAILABLE:
            try:
                # Download punkt tokenizer if not already available
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                try:
                    nltk.download('punkt', quiet=True)
                    self.logger.info("Downloaded NLTK punkt tokenizer")
                except Exception as e:
                    self.logger.warning(f"Failed to download NLTK punkt tokenizer: {e}")
                    global NLTK_AVAILABLE
                    NLTK_AVAILABLE = False
        
        if not NLTK_AVAILABLE:
            self.logger.info("NLTK not available, using regex-based sentence segmentation")
    
    def _setup_logging(self, log_level: int) -> logging.Logger:
        """Set up logging for the clause extractor."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_clause_definitions(self) -> None:
        """Load and parse the clause definitions JSON file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Clause definitions file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
            
            # Extract global configuration
            self.global_config = config_data.get('global_config', {})
            
            # Extract clause definitions
            self.clause_definitions = config_data.get('clause_definitions', {})
            
            # Log loaded clause types
            clause_types = list(self.clause_definitions.keys())
            self.logger.info(f"Loaded {len(clause_types)} clause types: {clause_types}")
            
            # Validate configuration
            self._validate_configuration()
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in clause definitions file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading clause definitions: {e}")
            raise
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration structure."""
        required_global_keys = ['default_confidence_threshold', 'default_case_sensitive']
        
        for key in required_global_keys:
            if key not in self.global_config:
                self.logger.warning(f"Missing global config key: {key}")
        
        for clause_type, definition in self.clause_definitions.items():
            required_keys = ['primary_keywords', 'secondary_keywords', 'negative_keywords']
            
            for key in required_keys:
                if key not in definition:
                    self.logger.warning(f"Missing key '{key}' in clause type '{clause_type}'")
                    definition[key] = []
    
    def _setup_preprocessing(self) -> None:
        """Initialize text preprocessing tools and compile regex patterns."""
        # Set up basic text preprocessing parameters
        self.default_case_sensitive = self.global_config.get('default_case_sensitive', False)
        self.default_confidence_threshold = self.global_config.get('default_confidence_threshold', 0.5)
        
        # Compile regex patterns for each clause type
        for clause_type, definition in self.clause_definitions.items():
            self._compile_patterns_for_clause(clause_type, definition)
            
            # Convert text patterns to regex patterns
            if "patterns" in definition and isinstance(definition["patterns"], list):
                definition["regex_patterns"] = self._convert_patterns_to_regex(definition["patterns"])
            else:
                definition["regex_patterns"] = []
        
        self.logger.debug("Text preprocessing setup completed")
    
    def _convert_patterns_to_regex(self, patterns: List[str]) -> List[re.Pattern]:
        """
        Convert text patterns to flexible regex patterns.
        
        Args:
            patterns: List of string patterns
            
        Returns:
            List of compiled regex patterns
        """
        compiled_patterns = []
        
        for pattern in patterns:
            if not pattern or not isinstance(pattern, str):
                continue
                
            # Clean the pattern
            clean_pattern = pattern.strip()
            if not clean_pattern:
                continue
                
            # Convert to a flexible regex pattern:
            # 1. Escape special regex characters
            escaped_pattern = re.escape(clean_pattern)
            
            # 2. Make whitespace flexible (match any amount of whitespace)
            flexible_pattern = escaped_pattern.replace("\\ ", "\\s+")
            
            # 3. Add word boundary markers for better precision
            if not flexible_pattern.startswith("\\b"):
                flexible_pattern = "\\b" + flexible_pattern
            if not flexible_pattern.endswith("\\b"):
                flexible_pattern = flexible_pattern + "\\b"
            
            # 4. Make punctuation optional by replacing them with optional groups
            # This handles variations in punctuation
            for punct in ["\\.","\\,","\\;","\\:","\\-","\\!"]:
                flexible_pattern = flexible_pattern.replace(punct, f"{punct}?")
            
            try:
                # Compile with IGNORECASE and DOTALL flags
                # IGNORECASE: Match regardless of case
                # DOTALL: Allow . to match newlines
                compiled_pattern = re.compile(flexible_pattern, re.IGNORECASE | re.DOTALL)
                compiled_patterns.append(compiled_pattern)
            except re.error as e:
                self.logger.warning(f"Failed to compile pattern '{pattern}': {e}")
        
        return compiled_patterns
    
    def match_patterns(self, text: str, clause_name: str) -> List[str]:
        """
        Match text against patterns for a specific clause type.
        
        Args:
            text: Text to match
            clause_name: Name of the clause to match patterns for
            
        Returns:
            List of matched pattern strings
        """
        if not text or not clause_name or clause_name not in self.clause_definitions:
            return []
        
        # Get the clause definition
        definition = self.clause_definitions[clause_name]
        
        # Get the regex patterns for this clause
        regex_patterns = definition.get("regex_patterns", [])
        
        # Also check for structured pattern objects
        structured_patterns = definition.get("patterns", [])
        if structured_patterns and isinstance(structured_patterns, list):
            for pattern_obj in structured_patterns:
                if isinstance(pattern_obj, dict) and "regex" in pattern_obj:
                    try:
                        # Use the regex directly from the pattern object
                        pattern_regex = pattern_obj["regex"]
                        compiled_pattern = re.compile(pattern_regex, re.IGNORECASE)
                        if compiled_pattern.search(text):
                            return [pattern_regex]  # Return immediately if we find a match
                    except re.error as e:
                        self.logger.warning(f"Invalid regex in pattern object: {e}")
        
        # Match against the converted patterns
        matched_patterns = []
        original_patterns = definition.get("patterns", [])
        
        for i, pattern in enumerate(regex_patterns):
            if pattern.search(text):
                # Add the original pattern to the matched list
                if i < len(original_patterns):
                    matched_patterns.append(original_patterns[i])
                
        return matched_patterns
    
    def _preprocess_text(self, text: str) -> str:
        """Apply basic text preprocessing."""
        if not text:
            return ""
        
        # Remove extra whitespace
        processed_text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize quotes and dashes
        processed_text = processed_text.replace('"', '"').replace('"', '"')
        processed_text = processed_text.replace(''', "'").replace(''', "'")
        processed_text = processed_text.replace('–', '-').replace('—', '-')
        
        return processed_text
    
    def get_clause_types(self) -> List[str]:
        """Get a list of all available clause types."""
        return list(self.clause_definitions.keys())
    
    def get_clause_definition(self, clause_type: str) -> Optional[Dict]:
        """Get the definition for a specific clause type."""
        return self.clause_definitions.get(clause_type)
    
    def segment_text(
        self, 
        text: str, 
        use_sliding_window: bool = True, 
        max_window_size: int = 3
    ) -> List[Dict]:
        """
        Segment text into sentences and create sliding windows.
        
        Args:
            text: Input text to segment
            use_sliding_window: Whether to create sliding windows of sentences
            max_window_size: Maximum number of sentences in a window (1-3)
            
        Returns:
            List of segment dictionaries with segment_id, start_index, end_index, text
        """
        if not text or not text.strip():
            return []
        
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # Generate segments
        segments = []
        segment_id = 0
        
        if use_sliding_window:
            # Create sliding windows
            max_window_size = max(1, min(max_window_size, 3))  # Clamp to 1-3
            
            for window_size in range(1, max_window_size + 1):
                for start_idx in range(len(sentences) - window_size + 1):
                    end_idx = start_idx + window_size - 1
                    
                    # Combine sentences in the window
                    window_text = ' '.join(sentences[start_idx:end_idx + 1])
                    
                    segments.append({
                        "segment_id": segment_id,
                        "start_index": start_idx,
                        "end_index": end_idx,
                        "text": window_text.strip()
                    })
                    segment_id += 1
        else:
            # Single sentence segments only
            for idx, sentence in enumerate(sentences):
                segments.append({
                    "segment_id": segment_id,
                    "start_index": idx,
                    "end_index": idx,
                    "text": sentence.strip()
                })
                segment_id += 1
        
        self.logger.debug(f"Created {len(segments)} text segments from {len(sentences)} sentences")
        return segments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using NLTK or regex fallback.
        
        Args:
            text: Input text to split
            
        Returns:
            List of sentence strings
        """
        text = text.strip()
        if not text:
            return []
        
        # Use NLTK if available
        if NLTK_AVAILABLE:
            try:
                sentences = sent_tokenize(text)
                # Filter out very short sentences (likely artifacts)
                sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
                return sentences
            except Exception as e:
                self.logger.warning(f"NLTK sentence splitting failed: {e}, falling back to regex")
        
        # Regex-based fallback
        return self._regex_sentence_split(text)
    
    def _regex_sentence_split(self, text: str) -> List[str]:
        """
        Split text into sentences using regex patterns.
        
        Args:
            text: Input text to split
            
        Returns:
            List of sentence strings
        """
        # Sentence boundary patterns
        sentence_endings = r'[.!?]+'
        
        # Abbreviation patterns to avoid splitting on
        abbreviations = r'\b(?:Mr|Mrs|Ms|Dr|Prof|Corp|Inc|Ltd|Co|vs|etc|al|Jr|Sr|Ph\.D|M\.D|B\.A|M\.A)\.'
        
        # Split on sentence endings, but preserve the ending punctuation
        sentences = re.split(f'({sentence_endings})', text)
        
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            # Check if this looks like an abbreviation
            if re.search(abbreviations, sentence) and len(sentence) < 50:
                # Likely an abbreviation, combine with next sentence
                if combined_sentences:
                    combined_sentences[-1] += ' ' + sentence
                else:
                    combined_sentences.append(sentence)
            else:
                combined_sentences.append(sentence)
        
        # Handle the last element if odd number of splits
        if len(sentences) % 2 == 1:
            last_sentence = sentences[-1].strip()
            if last_sentence:
                if combined_sentences:
                    combined_sentences[-1] += ' ' + last_sentence
                else:
                    combined_sentences.append(last_sentence)
        
        # Filter and clean sentences
        final_sentences = []
        for sentence in combined_sentences:
            sentence = sentence.strip()
            # Filter out very short sentences and clean up whitespace
            if len(sentence) > 10:
                sentence = re.sub(r'\s+', ' ', sentence)
                final_sentences.append(sentence)
        
        return final_sentences
    
    def extract_clauses(self, text: str) -> List[Dict]:
        """
        Extract clauses from the given text using keyword matching and confidence scoring.
        
        Args:
            text: The contract text to analyze
            
        Returns:
            List of dictionaries containing clause information
        """
        if not text or not text.strip():
            return []
        
        # Preprocess the text
        preprocessed_text = self._preprocess_text(text)
        
        # Segment the text into sentence windows
        segments = self.segment_text(preprocessed_text)
        
        if not segments:
            return []
        
        # Extract clauses from each segment
        extracted_clauses = []
        
        for segment in segments:
            segment_text = segment["text"]
            segment_id = segment["segment_id"]
            
            # Check each clause type against the segment
            for clause_type, definition in self.clause_definitions.items():
                confidence = self._calculate_confidence(segment_text, clause_type, definition)
                
                # Check if confidence meets minimum threshold
                min_threshold = definition.get("minimum_confidence_threshold", 
                                             self.global_config.get("default_confidence_threshold", 0.5))
                
                if confidence >= min_threshold:
                    extracted_clauses.append({
                        "clause_type": clause_type,
                        "segment_id": segment_id,
                        "text": segment_text,
                        "confidence": confidence
                    })
        
        # Sort by confidence (highest first)
        extracted_clauses.sort(key=lambda x: x["confidence"], reverse=True)
        
        self.logger.debug(f"Extracted {len(extracted_clauses)} clauses from {len(segments)} segments")
        
        return extracted_clauses
    
    def _calculate_confidence(self, text: str, clause_type: str, definition: Dict) -> float:
        """
        Calculate confidence score for a text segment matching a clause type.
        
        Args:
            text: The text segment to analyze
            clause_type: The type of clause being matched
            definition: The clause definition dictionary
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not text:
            return 0.0
        
        # Get compiled patterns for this clause type
        patterns = self.compiled_patterns.get(clause_type, {})
        
        # Check for negative keywords first
        negative_pattern = patterns.get("negative")
        if negative_pattern and negative_pattern.search(text):
            self.logger.debug(f"Negative keyword found in {clause_type}, rejecting")
            return 0.0
        
        # Track if we have any matches at all
        has_primary_match = False
        has_pattern_match = False
        
        # Calculate confidence based on keyword matches
        confidence_weights = definition.get("confidence_weights", {})
        total_confidence = 0.0
        
        # Primary keyword match
        primary_pattern = patterns.get("primary")
        primary_weight = confidence_weights.get("primary_keyword_match", 0.4)
        
        if primary_pattern and primary_pattern.search(text):
            primary_matches = len(primary_pattern.findall(text))
            primary_score = min(1.0, primary_matches * primary_weight)
            total_confidence += primary_score
            has_primary_match = True
        
        # Secondary keyword match (optional boost)
        secondary_pattern = patterns.get("secondary")
        if secondary_pattern:
            secondary_weight = confidence_weights.get("secondary_keyword_match", 0.2)
            secondary_matches = len(secondary_pattern.findall(text))
            secondary_score = min(1.0, secondary_matches * secondary_weight)
            total_confidence += secondary_score
        
        # Pattern matching from string patterns
        pattern_weight = confidence_weights.get("pattern_match", 0.25)
        pattern_boost_per_match = 0.2  # Boost per matched pattern
        
        # Match text against patterns defined for this clause
        matched_patterns = self.match_patterns(text, clause_type)
        
        if matched_patterns:
            has_pattern_match = True
            # Add bonus for each pattern match
            pattern_score = min(1.0, len(matched_patterns) * pattern_boost_per_match)
            total_confidence += pattern_score
            
            self.logger.debug(f"Matched patterns for {clause_type}: {matched_patterns}")
        
        # Context clues (optional boost)
        context_clues = definition.get("context_clues", [])
        if context_clues:
            context_weight = confidence_weights.get("context_clue_match", 0.1)
            context_matches = 0
            
            for clue in context_clues:
                case_sensitive = definition.get("case_sensitive", self.default_case_sensitive)
                flags = 0 if case_sensitive else re.IGNORECASE
                
                try:
                    clue_pattern = re.compile(r'\b' + re.escape(clue) + r'\b', flags)
                    if clue_pattern.search(text):
                        context_matches += 1
                except re.error:
                    pass
            
            if context_matches > 0:
                context_score = min(1.0, context_matches * context_weight)
                total_confidence += context_score
        
        # Check if we have any match at all
        if not has_primary_match and not has_pattern_match:
            # Neither primary keywords nor patterns matched
            return 0.0
        
        # Normalize confidence to be between 0.0 and 1.0
        total_confidence = min(1.0, max(0.0, total_confidence))
        
        self.logger.debug(f"Calculated confidence {total_confidence:.3f} for {clause_type}")
        
        return total_confidence
    
    def _compile_patterns_for_clause(self, clause_type: str, definition: Dict) -> None:
        """Compile regex patterns for a specific clause type."""
        case_sensitive = definition.get('case_sensitive', self.default_case_sensitive)
        flags = 0 if case_sensitive else re.IGNORECASE
        
        patterns = {}
        
        # Compile primary keyword patterns
        primary_keywords = definition.get('primary_keywords', [])
        if primary_keywords:
            primary_pattern = '|'.join(re.escape(keyword) for keyword in primary_keywords)
            patterns['primary'] = re.compile(f'\\b({primary_pattern})\\b', flags)
        
        # Compile secondary keyword patterns
        secondary_keywords = definition.get('secondary_keywords', [])
        if secondary_keywords:
            secondary_pattern = '|'.join(re.escape(keyword) for keyword in secondary_keywords)
            patterns['secondary'] = re.compile(f'\\b({secondary_pattern})\\b', flags)
        
        # Compile negative keyword patterns
        negative_keywords = definition.get('negative_keywords', [])
        if negative_keywords:
            negative_pattern = '|'.join(re.escape(keyword) for keyword in negative_keywords)
            patterns['negative'] = re.compile(f'\\b({negative_pattern})\\b', flags)
        
        self.compiled_patterns[clause_type] = patterns
        self.logger.debug(f"Compiled patterns for clause type: {clause_type}")