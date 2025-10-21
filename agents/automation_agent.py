"""Automation Agent for Composio Workflow Integration.
This module provides an agent that integrates with Composio workflows,
allowing automated execution of workflows with proper error handling
and configuration management.
"""
import os
import io
import re
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CandidateProfile:
    """Structured representation of a parsed candidate profile.

    Attributes:
        name: Candidate full name, if detected
        email: Candidate email address, if detected
        phone: Candidate phone number, if detected
        source_email_id: The Gmail message/thread identifier
        attachment_name: The original resume filename
        filetype: Attachment file extension
        raw_text_preview: First 500 chars of extracted text for debugging
        metadata: Any additional fields parsed
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source_email_id: Optional[str] = None
    attachment_name: Optional[str] = None
    filetype: Optional[str] = None
    raw_text_preview: Optional[str] = None
    metadata: Dict[str, Any] = None


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
        - COMPOSIO_AUTH_CONFIG_ID (optional): Auth config for connected app
        - COMPOSIO_CONNECTED_ACCOUNT_ID (optional): Connected account id

        Raises:
            ValueError: If COMPOSIO_API_KEY environment variable is not set
        """
        self.api_key = os.getenv('COMPOSIO_API_KEY')
        self.workflow_id = os.getenv('COMPOSIO_WORKFLOW_ID')
        self.auth_config_id = os.getenv('COMPOSIO_AUTH_CONFIG_ID')
        self.connected_account_id = os.getenv('COMPOSIO_CONNECTED_ACCOUNT_ID')

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

    def parse_gmail_resumes(self, query: Optional[str] = None, max_messages: int = 50) -> List[Dict[str, Any]]:
        """Fetch resumes from Gmail via Composio and extract basic candidate profiles.

        This method uses the Composio Gmail tool with a connected Google account to
        search for recent emails that contain resume-like attachments (PDF or DOCX),
        downloads those attachments via the tool, performs simple text extraction,
        and parses basic candidate details such as name, email, and phone.

        Environment variables used:
        - COMPOSIO_AUTH_CONFIG_ID: The Composio auth configuration ID for Gmail
        - COMPOSIO_CONNECTED_ACCOUNT_ID: The connected account ID for Gmail

        Args:
            query: Optional Gmail search query. If not provided, a default query is used
                to find messages with PDF/DOCX attachments likely to be resumes.
            max_messages: Maximum number of messages to scan.

        Returns:
            List[Dict[str, Any]]: List of candidate profiles with parsed fields and metadata.

        Notes:
            - This is a lightweight parser intended for quick triage. For production,
              consider richer parsing libraries and ML-based resume parsing.
            - Requires that your Composio project has Gmail connected and authorized.
        """
        # Lazy imports for optional dependencies
        try:
            from composio import Composio
        except ImportError:
            raise ImportError("Composio package not found. Install it with: pip install composio")

        # Validate connected account configuration
        if not self.auth_config_id or not self.connected_account_id:
            raise ValueError(
                "COMPOSIO_AUTH_CONFIG_ID and COMPOSIO_CONNECTED_ACCOUNT_ID are required to use Gmail tool."
            )

        client = Composio(api_key=self.api_key)

        # Default Gmail search query to find resume attachments
        default_query = (
            'has:attachment (filename:pdf OR filename:docx OR filename:doc) '
            '(-in:chats) newer_than:365d'
        )
        gmail_query = query or default_query

        # Helper regexes for parsing
        email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        phone_re = re.compile(r"(?:(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4})")
        name_hint_re = re.compile(r"(?i)name\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})")

        def extract_text_from_bytes(data: bytes, ext: str) -> str:
            """Best-effort text extraction for pdf/docx/doc without heavy deps.

            - For PDF: uses a naive bytes->text fallback (may be limited)
            - For DOCX: attempts to unzip and read document.xml text
            - For others: decode as utf-8 with replacement
            """
            try:
                if ext.lower() == 'pdf':
                    # Minimalistic heuristic extraction; recommend pdfminer.six for quality
                    try:
                        import pdfminer.high_level as pdf_high
                        with io.BytesIO(data) as bio:
                            return pdf_high.extract_text(bio) or ''
                    except Exception:
                        return data.decode('latin-1', errors='ignore')
                if ext.lower() == 'docx':
                    import zipfile
                    with io.BytesIO(data) as bio:
                        with zipfile.ZipFile(bio) as zf:
                            xml = zf.read('word/document.xml').decode('utf-8', errors='ignore')
                            # Strip XML tags crudely
                            return re.sub(r'<[^>]+>', ' ', xml)
                # Fallback
                return data.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.debug(f"Extraction failed for .{ext}: {e}")
                return ''

        def parse_fields(text: str) -> Dict[str, Optional[str]]:
            email = (email_re.search(text) or [None]) if isinstance(email_re.search(text), tuple) else email_re.search(text)
            email_val = email.group(0) if email else None
            phone = phone_re.search(text)
            phone_val = phone.group(0) if phone else None
            name_match = name_hint_re.search(text)
            name_val = name_match.group(1) if name_match else None
            return {"name": name_val, "email": email_val, "phone": phone_val}

        results: List[Dict[str, Any]] = []

        # Use Composio Gmail tool via tools API
        try:
            # 1) Search messages
            logger.info("Searching Gmail messages with resume attachments via Composio tool...")
            search_resp = client.tools.execute(
                tool_name="gmail_search_messages",
                input_params={
                    "q": gmail_query,
                    "maxResults": max_messages,
                },
                auth_config_id=self.auth_config_id,
                connected_account_id=self.connected_account_id,
            )

            messages = []
            if isinstance(search_resp, dict):
                # Composio often wraps tool response under 'result' or returns raw
                messages = search_resp.get('result') or search_resp.get('messages') or []
            elif isinstance(search_resp, list):
                messages = search_resp

            # Normalize to list of dicts with id/threadId
            normalized = []
            for m in messages:
                if isinstance(m, dict) and (m.get('id') or m.get('messageId')):
                    normalized.append(m)
                elif isinstance(m, str):
                    normalized.append({"id": m})
            messages = normalized

            logger.info(f"Found {len(messages)} messages to inspect")

            # 2) For each message, list attachments and download resume-like files
            for msg in messages:
                message_id = msg.get('id') or msg.get('messageId')
                if not message_id:
                    continue

                # List attachments for the message
                att_list_resp = client.tools.execute(
                    tool_name="gmail_list_attachments",
                    input_params={"messageId": message_id},
                    auth_config_id=self.auth_config_id,
                    connected_account_id=self.connected_account_id,
                )
                attachments = []
                if isinstance(att_list_resp, dict):
                    attachments = att_list_resp.get('result') or att_list_resp.get('attachments') or []
                elif isinstance(att_list_resp, list):
                    attachments = att_list_resp

                for att in attachments:
                    filename = att.get('filename') or ''
                    att_id = att.get('attachmentId') or att.get('id')
                    if not filename or not att_id:
                        continue

                    ext = filename.split('.')[-1].lower()
                    if ext not in {"pdf", "docx", "doc"}:
                        continue

                    # Download attachment bytes
                    dl_resp = client.tools.execute(
                        tool_name="gmail_get_attachment",
                        input_params={
                            "messageId": message_id,
                            "attachmentId": att_id,
                        },
                        auth_config_id=self.auth_config_id,
                        connected_account_id=self.connected_account_id,
                    )

                    # Composio may base64-encode or return bytes/JSON
                    data_bytes: Optional[bytes] = None
                    if isinstance(dl_resp, dict):
                        payload = dl_resp.get('result') or dl_resp
                        # Try common fields: 'data' base64, or 'content' bytes
                        b64 = payload.get('data') if isinstance(payload, dict) else None
                        if b64:
                            import base64
                            try:
                                data_bytes = base64.b64decode(b64)
                            except Exception:
                                data_bytes = None
                        content = payload.get('content') if isinstance(payload, dict) else None
                        if content and data_bytes is None:
                            if isinstance(content, str):
                                data_bytes = content.encode('latin-1', errors='ignore')
                            elif isinstance(content, (bytes, bytearray)):
                                data_bytes = bytes(content)
                    elif isinstance(dl_resp, (bytes, bytearray)):
                        data_bytes = bytes(dl_resp)

                    if not data_bytes:
                        logger.debug("Skipping attachment due to empty content")
                        continue

                    # Extract text and parse
                    text = extract_text_from_bytes(data_bytes, ext)
                    fields = parse_fields(text)

                    profile = CandidateProfile(
                        name=fields.get('name'),
                        email=fields.get('email'),
                        phone=fields.get('phone'),
                        source_email_id=message_id,
                        attachment_name=filename,
                        filetype=ext,
                        raw_text_preview=(text[:500] if text else None),
                        metadata={"chars": len(text)}
                    )
                    results.append(asdict(profile))

        except Exception as e:
            logger.error(f"Failed to parse resumes from Gmail: {e}")
            raise RuntimeError
