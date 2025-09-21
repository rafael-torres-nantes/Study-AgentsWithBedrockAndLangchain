"""
MCP Tools - Base Classes and Utilities
Module with base classes and utilities for MCP tools.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Logger configuration
logger = logging.getLogger(__name__)


class MCPToolBase(ABC):
    """
    Abstract base class for all MCP tools.
    Defines common interface and shared functionalities.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"mcp_tool.{name}")
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Executes the main functionality of the tool.
        Must be implemented by each specific tool.
        
        Returns:
            Dict[str, Any]: Execution result
        """
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validates input parameters.
        Can be overridden by specific tools.
        
        Returns:
            bool: True if valid, False otherwise
        """
        return True
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """
        Formats the response in MCP JSON standard.
        
        Args:
            result: Dictionary with execution result
            
        Returns:
            str: Formatted JSON
        """
        try:
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error formatting response: {e}")
            return json.dumps({
                "error": "Response formatting error",
                "details": str(e)
            }, ensure_ascii=False, indent=2)
    
    def handle_error(self, error: Exception, context: Optional[Dict] = None) -> str:
        """
        Handles errors in a standardized way.
        
        Args:
            error: Caught exception
            context: Additional error context
            
        Returns:
            str: JSON with error information
        """
        self.logger.error(f"Error in tool {self.name}: {error}")
        
        error_response = {
            "error": f"Error executing tool {self.name}",
            "details": str(error),
            "tool": self.name
        }
        
        if context:
            error_response.update(context)
        
        return self.format_response(error_response)
    
    def __call__(self, *args, **kwargs) -> str:
        """
        Allows the tool to be called directly.
        Implements complete flow: validation → execution → formatting.
        """
        try:
            # Input validation
            if not self.validate_input(*args, **kwargs):
                return self.handle_error(
                    ValueError("Invalid input parameters"),
                    {"received_parameters": {"args": args, "kwargs": kwargs}}
                )
            
            # Tool execution
            result = self.execute(*args, **kwargs)
            
            # Response formatting
            return self.format_response(result)
            
        except Exception as e:
            return self.handle_error(e, {"parameters": {"args": args, "kwargs": kwargs}})


class MCPResponseBuilder:
    """
    Builder for constructing standardized MCP tool responses.
    """
    
    def __init__(self, response_type: str):
        self.response = {
            "response_type": response_type
        }
    
    def add_input_info(self, **kwargs) -> 'MCPResponseBuilder':
        """Adds information about the processed input."""
        for key, value in kwargs.items():
            self.response[f"{key}"] = value
        return self
    
    def add_result(self, **kwargs) -> 'MCPResponseBuilder':
        """Adds operation results."""
        for key, value in kwargs.items():
            self.response[key] = value
        return self
    
    def add_summary(self, summary: str) -> 'MCPResponseBuilder':
        """Adds operation summary."""
        self.response["summary"] = summary
        return self
    
    def build(self) -> Dict[str, Any]:
        """Builds the final response dictionary."""
        return self.response


class MCPToolValidator:
    """
    Centralized validator for MCP tool parameters.
    """
    
    @staticmethod
    def validate_text(text: str, field_name: str = "text") -> bool:
        """Validates that text is not empty."""
        return bool(text and text.strip())
    
    @staticmethod
    def validate_number(value: Any, field_name: str = "number") -> bool:
        """Validates that value is a valid number."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_operation(operation: str, valid_operations: list) -> bool:
        """Validates that operation is in the list of valid operations."""
        return operation in valid_operations
    
    @staticmethod
    def validate_algorithm(algorithm: str, valid_algorithms: list) -> bool:
        """Validates that algorithm is in the list of valid algorithms."""
        return algorithm in valid_algorithms
