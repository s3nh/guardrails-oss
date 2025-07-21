#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Guardrail class definition.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union


class BaseGuardrail(ABC):
    """
    Base class for all guardrail implementations.
    """
    
    def __init__(self):
        """Initialize the base guardrail."""
        self.safety_message = "I cannot fulfill this request due to safety concerns."
    
    def get_safety_message(self) -> str:
        """
        Return the safety message to use when the guardrail blocks a request.
        
        Returns:
            str: Safety message
        """
        return self.safety_message
    
    def set_safety_message(self, message: str):
        """
        Set a custom safety message.
        
        Args:
            message (str): Custom safety message
        """
        self.safety_message = message
    
    def preprocess(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Process the prompt before sending it to the model.
        
        Args:
            prompt (str): User input prompt
            **kwargs: Additional context parameters
            
        Returns:
            Optional[str]: Processed prompt or None if blocked
        """
        # Default implementation passes through the prompt unchanged
        return prompt
    
    def postprocess(self, prompt: str, response: str, **kwargs) -> Optional[str]:
        """
        Process the model's response before returning it to the user.
        
        Args:
            prompt (str): Original user prompt
            response (str): Model's response
            **kwargs: Additional context parameters
            
        Returns:
            Optional[str]: Processed response or None if blocked
        """
        # Default implementation passes through the response unchanged
        return response
