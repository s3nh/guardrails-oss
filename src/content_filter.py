#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content filtering guardrail to detect and block harmful outputs.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from .base import BaseGuardrail

logger = logging.getLogger(__name__)


class ContentFilterGuardrail(BaseGuardrail):
    """
    Guardrail that evaluates content for harmful, unsafe, or prohibited content.
    """
    
    def __init__(self, client=None, risk_threshold: float = 0.7, categories: List[str] = None):
        """
        Initialize the content filter guardrail.
        
        Args:
            client: Gemini client for content evaluation
            risk_threshold (float): Risk score threshold (0.0-1.0) above which content is blocked
            categories (List[str], optional): Categories of content to evaluate.
                Defaults to ["harmful", "illegal", "unethical", "sensitive"].
        """
        super().__init__()
        self.client = client
        self.risk_threshold = risk_threshold
        self.categories = categories or ["harmful", "illegal", "unethical", "sensitive"]
        self.safety_message = "I cannot fulfill this request as it may result in content that violates safety guidelines."
        
    def preprocess(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Check if the input prompt is requesting harmful content.
        
        Args:
            prompt (str): User input prompt
            **kwargs: Additional context parameters
            
        Returns:
            Optional[str]: Original prompt if safe, None if blocked
        """
        if self.client is None:
            logger.warning("Content filter has no client, skipping preprocessing check")
            return prompt
        
        safety_score = self.check_safety(prompt)
        if safety_score >= self.risk_threshold:
            logger.warning(f"Content filter blocked prompt with risk score {safety_score}")
            return None
        
        return prompt
    
    def postprocess(self, prompt: str, response: str, **kwargs) -> Optional[str]:
        """
        Check if the generated response contains harmful content.
        
        Args:
            prompt (str): Original user prompt
            response (str): Model's response
            **kwargs: Additional context parameters
            
        Returns:
            Optional[str]: Original response if safe, None if blocked
        """
        if self.client is None:
            logger.warning("Content filter has no client, skipping postprocessing check")
            return response
        
        safety_score = self.check_safety(response)
        if safety_score >= self.risk_threshold:
            logger.warning(f"Content filter blocked response with risk score {safety_score}")
            return None
        
        return response
    
    def check_safety(self, content: str) -> float:
        """
        Check content safety using the model itself.
        
        Args:
            content (str): Content to evaluate
            
        Returns:
            float: Risk score between 0.0 (safe) and 1.0 (unsafe)
        """
        try:
            # Use a separate Gemini call to evaluate content
            risk_detection_prompt = f"""
            You are a content risk analyzer. Evaluate if the following content contains any of these risks:
            - Harmful Content: Content that could cause harm to individuals or groups
            - Illegal Content: Instructions or information for illegal activities
            - Unethical Content: Content that violates ethical standards
            - Sensitive Content: Content that contains private or sensitive information

            For each category, assign a risk score (0.0-1.0) and provide brief justification.
            Format your response as valid JSON:
            {{
              "harmful": {{"score": X, "reason": "brief reason"}},
              "illegal": {{"score": X, "reason": "brief reason"}},
              "unethical": {{"score": X, "reason": "brief reason"}},
              "sensitive": {{"score": X, "reason": "brief reason"}},
              "overall_risk": X
            }}

            Content to evaluate: {content}
            """
            
            # Generate safety evaluation
            safety_result = self.client.generate(risk_detection_prompt)
            
            # Extract JSON response
            try:
                # Find JSON in the response (model might add extra text)
                json_start = safety_result.find('{')
                json_end = safety_result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    safety_json = safety_result[json_start:json_end]
                    safety_data = json.loads(safety_json)
                    
                    # Return overall risk or calculate it
                    if "overall_risk" in safety_data:
                        return float(safety_data["overall_risk"])
                    else:
                        # Calculate overall risk as maximum of individual risks
                        risks = [
                            safety_data.get("harmful", {}).get("score", 0),
                            safety_data.get("illegal", {}).get("score", 0),
                            safety_data.get("unethical", {}).get("score", 0),
                            safety_data.get("sensitive", {}).get("score", 0)
                        ]
                        return max([float(r) for r in risks if r is not None])
                        
            except Exception as e:
                logger.error(f"Failed to parse safety result JSON: {e}")
                # Default to moderately risky if parsing fails
                return 0.5
                
        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            # Default to safe if check fails completely
            return 0.0
