"""
Enhanced CSS Evaluator - Migrated from the original CSS evaluation framework
Evaluates CSS consolidation tasks with intelligent pattern detection
"""

import re
from typing import Dict, List, Any
from pathlib import Path
import os

try:
    from bs4 import BeautifulSoup
except ImportError:
    # Fallback if BeautifulSoup is not available
    BeautifulSoup = None


class EnhancedCSSEvaluator:
    """Enhanced CSS evaluator with intelligent pattern detection"""
    
    def __init__(self):
        self.style_frequency = {}
        self.patterns = {
            "repetitive": [],
            "data_driven": [],
            "positioning": [],
            "unique": []
        }
    
    def evaluate(self, baseline_files: Dict[str, str], solution_files: Dict[str, str]) -> Dict[str, Any]:
        """Main evaluation method"""
        
        # Analyze baseline
        baseline_results = self._analyze_files(baseline_files)
        
        # Analyze solution
        solution_results = self._analyze_files(solution_files)
        
        # Calculate scores
        scores = self._calculate_scores(baseline_results, solution_results)
        
        return {
            "scores": scores["breakdown"],
            "total_score": scores["total"],
            "baseline": baseline_results,
            "solution": solution_results,
            "improvements": self._generate_improvements(baseline_results, solution_results),
            "evaluation_type": "rule_based_css"
        }
    
    def _analyze_files(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze HTML/CSS files for consolidation opportunities"""
        
        results = {
            "total_inline_styles": 0,
            "repetitive": 0,
            "data_driven": 0,
            "positioning": 0,
            "unique": 0,
            "ie_hacks": 0,
            "font_tags": 0,
            "style_blocks": 0,
            "patterns": {},
            "file_results": {}
        }
        
        # Reset for new analysis
        self.style_frequency = {}
        self.patterns = {
            "repetitive": [],
            "data_driven": [],
            "positioning": [],
            "unique": []
        }
        
        for filename, content in files.items():
            if filename.endswith('.html'):
                file_results = self._analyze_html(content)
                results["file_results"][filename] = file_results
                
                # Aggregate results
                for key in ["total_inline_styles", "repetitive", "data_driven", 
                           "positioning", "unique", "ie_hacks", "font_tags", "style_blocks"]:
                    results[key] += file_results.get(key, 0)
        
        # Categorize patterns
        self._categorize_patterns(results)
        
        return results
    
    def _analyze_html(self, html_content: str) -> Dict[str, Any]:
        """Analyze a single HTML file"""
        
        if BeautifulSoup is None:
            # Fallback to regex analysis if BeautifulSoup not available
            return self._analyze_html_regex(html_content)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        results = {
            "total_inline_styles": 0,
            "repetitive": 0,
            "data_driven": 0,
            "positioning": 0,
            "unique": 0,
            "ie_hacks": 0,
            "font_tags": 0,
            "style_blocks": 0,
            "details": []
        }
        
        # Analyze inline styles
        for element in soup.find_all(attrs={"style": True}):
            if self._is_injected_element(element):
                continue
            
            style = element.get("style", "")
            normalized = self._normalize_style(style)
            
            results["total_inline_styles"] += 1
            
            if self._is_ie_hack(style):
                results["ie_hacks"] += 1
            
            # Track style frequency
            if normalized not in self.style_frequency:
                self.style_frequency[normalized] = []
            
            self.style_frequency[normalized].append({
                "element": element.name,
                "style": style,
                "context": self._get_element_context(element)
            })
        
        # Count font tags
        results["font_tags"] = len(soup.find_all("font"))
        
        # Count style blocks
        results["style_blocks"] = len(soup.find_all("style"))
        
        return results
    
    def _analyze_html_regex(self, html_content: str) -> Dict[str, Any]:
        """Fallback regex-based HTML analysis"""
        
        results = {
            "total_inline_styles": 0,
            "repetitive": 0,
            "data_driven": 0,
            "positioning": 0,
            "unique": 0,
            "ie_hacks": 0,
            "font_tags": 0,
            "style_blocks": 0,
            "details": []
        }
        
        # Find inline styles
        style_pattern = r'style\s*=\s*["\']([^"\']*)["\']'
        styles = re.findall(style_pattern, html_content, re.IGNORECASE)
        
        for style in styles:
            normalized = self._normalize_style(style)
            results["total_inline_styles"] += 1
            
            if self._is_ie_hack(style):
                results["ie_hacks"] += 1
            
            # Track frequency
            if normalized not in self.style_frequency:
                self.style_frequency[normalized] = []
            
            self.style_frequency[normalized].append({
                "element": "unknown",
                "style": style,
                "context": {}
            })
        
        # Count font tags
        font_pattern = r'<font[^>]*>'
        results["font_tags"] = len(re.findall(font_pattern, html_content, re.IGNORECASE))
        
        # Count style blocks
        style_block_pattern = r'<style[^>]*>.*?</style>'
        results["style_blocks"] = len(re.findall(style_block_pattern, html_content, re.IGNORECASE | re.DOTALL))
        
        return results
    
    def _normalize_style(self, style_string: str) -> str:
        """Normalize style by replacing values with placeholders"""
        return re.sub(r':\s*[^;]+', ': VALUE', style_string).strip().lower()
    
    def _is_data_driven_style(self, element_context: Dict) -> bool:
        """Check if style is data-driven (should be kept inline)"""
        # This is a simplified version - the original has more sophisticated detection
        text = element_context.get("text", "")
        return any([
            re.search(r'-?\$?\d+\.?\d*', text),  # Currency/numbers
            text.strip().startswith('-'),         # Negative values
            text.strip().startswith('+'),         # Positive values
        ])
    
    def _is_positioning_style(self, style_string: str) -> bool:
        """Check if style is positioning-related"""
        positioning_props = [
            'position', 'top', 'left', 'right', 'bottom',
            'margin', 'padding', 'float', 'clear',
            'transform', 'z-index'
        ]
        
        return any(prop in style_string.lower() for prop in positioning_props)
    
    def _is_ie_hack(self, style_string: str) -> bool:
        """Check if style contains IE-specific hacks"""
        ie_patterns = ['filter:', 'zoom:', r'\*[a-zA-Z]', r'_[a-zA-Z]']
        return any(re.search(pattern, style_string) for pattern in ie_patterns)
    
    def _is_injected_element(self, element) -> bool:
        """Check if element is part of injected metrics/header system"""
        if BeautifulSoup is None:
            return False
        
        # Check for injected IDs
        element_id = element.get('id', '')
        if element_id in ['globalHeader', 'metricsPanel', 'metricsContent', 'styleToggle', 'metricsToggle']:
            return True
        
        # Check if parent has injected ID
        parent = element.parent
        while parent:
            parent_id = parent.get('id', '') if hasattr(parent, 'get') else ''
            if parent_id in ['globalHeader', 'metricsPanel']:
                return True
            parent = parent.parent
        
        return False
    
    def _get_element_context(self, element) -> Dict:
        """Get context information about an element"""
        if BeautifulSoup is None:
            return {}
        
        parent = element.parent
        text = element.get_text().strip() if element else ""
        
        return {
            "tag": element.name,
            "text": text,
            "is_in_table": parent and parent.name in ['td', 'th'],
            "has_numeric_content": bool(re.search(r'\d', text)),
            "parent_tag": parent.name if parent else None
        }
    
    def _categorize_patterns(self, results: Dict[str, Any]):
        """Categorize style patterns by type"""
        
        for normalized, occurrences in self.style_frequency.items():
            if len(occurrences) > 1:
                # Repetitive pattern
                first_occurrence = occurrences[0]
                
                if self._is_data_driven_style(first_occurrence.get("context", {})):
                    results["data_driven"] += len(occurrences)
                    self.patterns["data_driven"].append({
                        "pattern": normalized,
                        "count": len(occurrences),
                        "example": first_occurrence["style"]
                    })
                elif self._is_positioning_style(first_occurrence["style"]):
                    results["positioning"] += len(occurrences)
                    self.patterns["positioning"].append({
                        "pattern": normalized,
                        "count": len(occurrences),
                        "example": first_occurrence["style"]
                    })
                else:
                    results["repetitive"] += len(occurrences)
                    self.patterns["repetitive"].append({
                        "pattern": normalized,
                        "count": len(occurrences),
                        "example": first_occurrence["style"]
                    })
            else:
                # Unique pattern
                occurrence = occurrences[0]
                if self._is_data_driven_style(occurrence.get("context", {})):
                    results["data_driven"] += 1
                    self.patterns["data_driven"].append({
                        "pattern": normalized,
                        "count": 1,
                        "example": occurrence["style"]
                    })
                elif self._is_positioning_style(occurrence["style"]):
                    results["positioning"] += 1
                    self.patterns["positioning"].append({
                        "pattern": normalized,
                        "count": 1,
                        "example": occurrence["style"]
                    })
                else:
                    results["unique"] += 1
                    self.patterns["unique"].append({
                        "pattern": normalized,
                        "count": 1,
                        "example": occurrence["style"]
                    })
        
        # Sort patterns by frequency
        for pattern_type in self.patterns:
            self.patterns[pattern_type].sort(key=lambda x: x["count"], reverse=True)
        
        results["patterns"] = self.patterns
    
    def _calculate_scores(self, baseline: Dict[str, Any], solution: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate evaluation scores based on improvements"""
        
        breakdown = {
            "pattern_consolidation": 0,
            "ie_hack_removal": 0,
            "font_tag_modernization": 0,
            "style_block_cleanup": 0,
            "smart_retention": 0
        }
        
        # Pattern Consolidation (40 points)
        if baseline["repetitive"] > 0:
            consolidation_rate = max(0, 
                (baseline["repetitive"] - solution["repetitive"]) / baseline["repetitive"]
            )
            breakdown["pattern_consolidation"] = round(consolidation_rate * 40)
        else:
            breakdown["pattern_consolidation"] = 40
        
        # IE Hack Removal (20 points)
        if baseline["ie_hacks"] > 0 and solution["ie_hacks"] == 0:
            breakdown["ie_hack_removal"] = 20
        elif baseline["ie_hacks"] == 0:
            breakdown["ie_hack_removal"] = 20
        
        # Font Tag Modernization (15 points)
        if baseline["font_tags"] > 0 and solution["font_tags"] == 0:
            breakdown["font_tag_modernization"] = 15
        elif baseline["font_tags"] == 0:
            breakdown["font_tag_modernization"] = 15
        
        # Style Block Cleanup (15 points)
        if baseline["style_blocks"] > 0 and solution["style_blocks"] == 0:
            breakdown["style_block_cleanup"] = 15
        elif baseline["style_blocks"] == 0:
            breakdown["style_block_cleanup"] = 15
        
        # Smart Retention (10 points)
        total_remaining = solution["total_inline_styles"]
        legitimate_remaining = solution["data_driven"] + solution["positioning"]
        
        if total_remaining > 0:
            legitimate_ratio = legitimate_remaining / total_remaining
            breakdown["smart_retention"] = round(legitimate_ratio * 10)
        else:
            breakdown["smart_retention"] = 10
        
        total_score = sum(breakdown.values())
        
        return {
            "breakdown": breakdown,
            "total": min(100, total_score)
        }
    
    def _generate_improvements(self, baseline: Dict[str, Any], solution: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions"""
        
        improvements = []
        
        if solution["repetitive"] > baseline["repetitive"] * 0.2:
            improvements.append(f"Consider consolidating {solution['repetitive']} remaining repetitive styles")
        
        if solution["ie_hacks"] > 0:
            improvements.append(f"Remove {solution['ie_hacks']} remaining IE-specific hacks")
        
        if solution["font_tags"] > 0:
            improvements.append(f"Modernize {solution['font_tags']} remaining <font> tags")
        
        if solution["style_blocks"] > 0:
            improvements.append(f"Move {solution['style_blocks']} <style> blocks to external CSS")
        
        # Positive feedback
        if solution["repetitive"] < baseline["repetitive"] * 0.8:
            improvements.append("Good job consolidating repetitive patterns!")
        
        if solution["data_driven"] >= baseline["data_driven"] * 0.8:
            improvements.append("Excellent retention of data-driven styles!")
        
        return improvements