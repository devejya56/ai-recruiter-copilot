"""Automation Agent for Composio Workflow Integration.

This module provides an agent that integrates with Composio workflows,
allowing automated execution of workflows with proper error handling
and configuration management.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomationAgent:
    """Agent for triggering and managing Composio workflows.
    
    This agent handles the integration with Composio's workflow system,
    providing a clean interface to trigger workflows with input data.
    It manages API authentication and provides robust error handling.
    
    Attributes:
        api_key (str): Composio API key for authentication (required)
        workflow_id (str): Default workflow ID to use (optional)
    
    Raises:
        ValueError: If COMPOSIO_API_KEY is not set in environment
    """
    
    def __init__(self):
        """Initialize the AutomationAgent with Composio credentials.
        
        Reads configuration from environment variables:
        - COMPOSIO_API_KEY (required): API key for Composio authentication
        - COMPOSIO_WORKFLOW_ID (optional): Default workflow ID to use
        
        Raises:
            ValueError: If COMPOSIO_API_KEY environment variable is not set
        """
        self.api_key = os.getenv('COMPOSIO_API_KEY')
        self.workflow_id = os.getenv('COMPOSIO_WORKFLOW_ID')
        
        if not self.api_key:
            raise ValueError(
                "COMPOSIO_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )
        
        logger.info("AutomationAgent initialized successfully")
        if self.workflow_id:
            logger.info(f"Default workflow ID: {self.workflow_id}")
        else:
            logger.info("No default workflow ID set")
    
    def run_workflow(
        self, 
        input_data: Dict[str, Any], 
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger a Composio workflow with the provided input data.
        
        This method sends a request to trigger a Composio workflow with the
        specified input data. It handles authentication, request formatting,
        and error handling.
        
        Args:
            input_data (Dict[str, Any]): Input data to pass to the workflow.
                Should be a dictionary containing workflow-specific parameters.
            workflow_id (Optional[str]): Specific workflow ID to trigger.
                If not provided, uses the default workflow_id from initialization.
        
        Returns:
            Dict[str, Any]: Response from the Composio API containing:
                - status: Execution status
                - workflow_id: ID of the executed workflow
                - execution_id: Unique execution identifier
                - result: Workflow execution result (if available)
        
        Raises:
            ValueError: If no workflow_id is provided and no default is set
            ConnectionError: If unable to connect to Composio API
            RuntimeError: If the API returns an error response
        
        Example:
            >>> agent = AutomationAgent()
            >>> result = agent.run_workflow(
            ...     input_data={'candidate': 'John Doe', 'role': 'Engineer'},
            ...     workflow_id='workflow_123'
            ... )
            >>> print(result['status'])
            'success'
        """
        # Determine which workflow ID to use
        target_workflow_id = workflow_id or self.workflow_id
        
        if not target_workflow_id:
            raise ValueError(
                "No workflow_id provided. Either pass workflow_id as parameter "
                "or set COMPOSIO_WORKFLOW_ID in environment variables."
            )
        
        logger.info(f"Triggering workflow: {target_workflow_id}")
        logger.debug(f"Input data: {input_data}")
        
        try:
            # Import composio client (lazy import to avoid dependency issues)
            try:
                from composio import Composio
            except ImportError:
                raise ImportError(
                    "Composio package not found. Install it with: pip install composio"
                )
            
            # Initialize Composio client
            client = Composio(api_key=self.api_key)
            
            # Trigger the workflow
            logger.info("Sending workflow execution request...")
            response = client.workflows.execute(
                workflow_id=target_workflow_id,
                input_data=input_data
            )
            
            logger.info(f"Workflow triggered successfully: {response.get('execution_id', 'N/A')}")
            return {
                'status': 'success',
                'workflow_id': target_workflow_id,
                'execution_id': response.get('execution_id'),
                'result': response.get('result'),
                'message': 'Workflow executed successfully'
            }
            
        except ImportError as e:
            logger.error(f"Import error: {str(e)}")
            raise
            
        except ConnectionError as e:
            logger.error(f"Connection error while accessing Composio API: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Composio API: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            raise RuntimeError(
                f"Workflow execution failed: {str(e)}"
            )
    
    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get the status of a workflow execution.
        
        Args:
            execution_id (str): The execution ID returned from run_workflow
        
        Returns:
            Dict[str, Any]: Current status of the workflow execution
        
        Raises:
            RuntimeError: If unable to retrieve workflow status
        """
        logger.info(f"Checking status for execution: {execution_id}")
        
        try:
            from composio import Composio
            
            client = Composio(api_key=self.api_key)
            status = client.workflows.get_execution_status(execution_id)
            
            logger.info(f"Status retrieved: {status.get('state', 'unknown')}")
            return status
            
        except Exception as e:
            logger.error(f"Error retrieving workflow status: {str(e)}")
            raise RuntimeError(
                f"Failed to get workflow status: {str(e)}"
            )


if __name__ == "__main__":
    # Example usage
    try:
        agent = AutomationAgent()
        
        # Example workflow execution
        sample_input = {
            'candidate_name': 'John Doe',
            'position': 'Senior Software Engineer',
            'action': 'schedule_interview'
        }
        
        result = agent.run_workflow(input_data=sample_input)
        print(f"Workflow Result: {result}")
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
