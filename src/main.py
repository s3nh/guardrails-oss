#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Gemini Guardrails Framework.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union

from .guardrails.base import BaseGuardrail
from .guardrails.content_filter import ContentFilterGuardrail
from .guardrails.injection_detector import InjectionDetectorGuardrail
from .guardrails.role_based import RoleBasedGuardrail
from .guardrails.sandbox import SandboxGuardrail
from .gemini.client import GeminiClient
from .utils.logging_utils import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

class SafeGeminiClient:
    """
    A client for interacting with Google's Gemini models with enhanced safety guardrails.
    """
    
    def __init__(self, config_path: str = None, api_key: str = None):
        """
        Initialize the SafeGeminiClient with configuration.
        
        Args:
            config_path (str, optional): Path to the guardrail configuration file.
                Defaults to 'config/guardrail_config.json'.
            api_key (str, optional): Google API key for Gemini access.
                If not provided, will look for GOOGLE_API_KEY environment variable.
        """
        # Load configuration
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'guardrail_config.json'
        )
        self.config = self._load_config()
        
        # Set up Gemini client
        api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass as parameter.")
        
        self.client = GeminiClient(
            api_key=api_key,
            model=self.config['gemini'].get('model', 'gemini-2.0-pro'),
            temperature=self.config['gemini'].get('temperature', 0.7),
            max_tokens=self.config['gemini'].get('max_tokens', 1024),
            safety_settings=self.config['gemini'].get('safety_settings', {})
        )
        
        # Initialize guardrails
        self.guardrails = []
        self._init_guardrails()
        
        logger.info("SafeGeminiClient initialized with %d guardrails", len(self.guardrails))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse configuration from the JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.debug("Configuration loaded from %s", self.config_path)
            return config
        except Exception as e:
            logger.error("Failed to load configuration: %s", str(e))
            # Use default configuration
            return {
                "guardrails": {
                    "content_filter": {"enabled": True},
                    "injection_detector": {"enabled": True},
                    "role_based": {"enabled": False},
                    "sandbox": {"enabled": True},
                    "circuit_breaker": {"enabled": True},
                    "logging": {"enabled": True}
                },
                "gemini": {
                    "model": "gemini-2.0-pro",
                    "temperature": 0.7,
                    "max_tokens": 1024,
                    "safety_settings": {}
                }
            }
    
    def _init_guardrails(self):
        """Initialize all enabled guardrails from configuration."""
        guardrail_config = self.config.get('guardrails', {})
        
        # Content filter guardrail
        if guardrail_config.get('content_filter', {}).get('enabled', False):
            self.guardrails.append(
                ContentFilterGuardrail(
                    client=self.client,
                    risk_threshold=guardrail_config.get('content_filter', {}).get('risk_threshold', 0.7),
                    categories=guardrail_config.get('content_filter', {}).get('categories', [])
                )
            )
        
        # Injection detector guardrail
        if guardrail_config.get('injection_detector', {}).get('enabled', False):
            self.guardrails.append(
                InjectionDetectorGuardrail(
                    detection_patterns=guardrail_config.get('injection_detector', {}).get('detection_patterns', []),
                    max_token_inspection=guardrail_config.get('injection_detector', {}).get('max_token_inspection', 50)
                )
            )
        
        # Role-based guardrail
        if guardrail_config.get('role_based', {}).get('enabled', False):
            self.guardrails.append(
                RoleBasedGuardrail(
                    client=self.client,
                    roles=guardrail_config.get('role_based', {}).get('roles', {})
                )
            )
        
        # Sandbox guardrail
        if guardrail_config.get('sandbox', {}).get('enabled', False):
            self.guardrails.append(
                SandboxGuardrail(
                    memory_isolation=guardrail_config.get('sandbox', {}).get('memory_isolation', True),
                    instruction_isolation=guardrail_config.get('sandbox', {}).get('instruction_isolation', True)
                )
            )
    
    def generate(self, prompt: str, role: str = "user") -> str:
        """
        Generate a safe response from Gemini using all configured guardrails.
        
        Args:
            prompt (str): User input prompt
            role (str, optional): User role for role-based access control.
                Defaults to "user".
                
        Returns:
            str: Safe response from Gemini or safety message
        """
        logger.info("Processing prompt with role: %s", role)
        
        # Apply pre-processing guardrails
        for guardrail in self.guardrails:
            if isinstance(guardrail, BaseGuardrail) and hasattr(guardrail, 'preprocess'):
                prompt_result = guardrail.preprocess(prompt, role=role)
                
                # If a guardrail returns None or a safety message, return it immediately
                if prompt_result is None:
                    safety_message = guardrail.get_safety_message()
                    logger.warning("Guardrail %s blocked the prompt", guardrail.__class__.__name__)
                    return safety_message
                
                # Otherwise, update the prompt with the processed version
                prompt = prompt_result
        
        # Generate response with the base model
        try:
            response = self.client.generate(prompt)
        except Exception as e:
            logger.error("Error generating response: %s", str(e))
            return "I apologize, but I encountered an error processing your request."
        
        # Apply post-processing guardrails
        for guardrail in self.guardrails:
            if isinstance(guardrail, BaseGuardrail) and hasattr(guardrail, 'postprocess'):
                response_result = guardrail.postprocess(prompt, response, role=role)
                
                # If a guardrail blocks the response, return its safety message
                if response_result is None:
                    safety_message = guardrail.get_safety_message()
                    logger.warning("Guardrail %s blocked the response", guardrail.__class__.__name__)
                    return safety_message
                
                # Otherwise, update the response with the processed version
                response = response_result
        
        return response
    
    def generate_stream(self, prompt: str, role: str = "user"):
        """
        Stream a safe response from Gemini using all configured guardrails.
        
        Args:
            prompt (str): User input prompt
            role (str, optional): User role for role-based access control.
                Defaults to "user".
                
        Yields:
            str: Tokens of the safe response or safety message
        """
        # Apply pre-processing guardrails
        for guardrail in self.guardrails:
            if isinstance(guardrail, BaseGuardrail) and hasattr(guardrail, 'preprocess'):
                prompt_result = guardrail.preprocess(prompt, role=role)
                
                # If a guardrail returns None or a safety message, yield it immediately
                if prompt_result is None:
                    safety_message = guardrail.get_safety_message()
                    logger.warning("Guardrail %s blocked the prompt", guardrail.__class__.__name__)
                    yield safety_message
                    return
                
                # Otherwise, update the prompt with the processed version
                prompt = prompt_result
        
        # Configure circuit breaker if enabled
        circuit_breaker_config = self.config.get('guardrails', {}).get('circuit_breaker', {})
        if circuit_breaker_config.get('enabled', False):
            check_interval = circuit_breaker_config.get('check_interval', 20)
            safety_threshold = circuit_breaker_config.get('safety_threshold', 0.8)
            
            # Stream response with circuit breaker
            response_buffer = ""
            token_count = 0
            
            try:
                for token in self.client.generate_stream(prompt):
                    response_buffer += token
                    token_count += 1
                    
                    # Check safety at intervals
                    if token_count % check_interval == 0:
                        is_safe = True
                        for guardrail in self.guardrails:
                            if isinstance(guardrail, ContentFilterGuardrail):
                                safety_score = guardrail.check_safety(response_buffer)
                                if safety_score < safety_threshold:
                                    is_safe = False
                                    break
                        
                        if not is_safe:
                            yield "\n\n[Generation stopped due to safety concerns]"
                            return
                    
                    yield token
            
            except Exception as e:
                logger.error("Error streaming response: %s", str(e))
                yield "\n\nI apologize, but I encountered an error processing your request."
        
        # Stream without circuit breaker
        else:
            try:
                for token in self.client.generate_stream(prompt):
                    yield token
            except Exception as e:
                logger.error("Error streaming response: %s", str(e))
                yield "\n\nI apologize, but I encountered an error processing your request."


if __name__ == "__main__":
    # Example usage
    client = SafeGeminiClient()
    response = client.generate("Tell me about quantum computing")
    print(response)
