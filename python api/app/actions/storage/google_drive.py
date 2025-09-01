"""Google Drive Storage Action

This module implements an action for interacting with Google Drive.
It can upload, download, list, and manage files in Google Drive.
"""

import logging
import io
import os
from typing import Any, Dict, Optional, List
from datetime import datetime

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class GoogleDriveAction(BaseAction):
    """Action for Google Drive file operations.

    This action supports:
    - File upload to Google Drive
    - File download from Google Drive
    - File listing and searching
    - Folder creation and management
    - File metadata retrieval
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.operation = config.get("operation", "upload")  # upload, download, list, create_folder, delete
        self.credentials_path = config.get("credentials_path", "")
        self.credentials_json = config.get("credentials_json", "")
        self.service_account_key = config.get("service_account_key", "")
        self.parent_folder_id = config.get("parent_folder_id", "")  # Root folder or specific folder
        self.file_name = config.get("file_name", "")
        self.file_id = config.get("file_id", "")
        self.mime_type = config.get("mime_type", "")
        self.convert_to_google_format = config.get("convert_to_google_format", False)

    async def validate_config(self) -> bool:
        """Validate Google Drive action configuration."""
        if not any([self.credentials_path, self.credentials_json, self.service_account_key]):
            raise ValueError("Google Drive credentials are required (credentials_path, credentials_json, or service_account_key)")

        valid_operations = ["upload", "download", "list", "create_folder", "delete", "get_metadata"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        if self.operation in ["upload", "download"] and not self.file_name:
            raise ValueError("file_name is required for upload/download operations")

        if self.operation == "download" and not self.file_id:
            raise ValueError("file_id is required for download operation")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the Google Drive operation."""
        try:
            # Initialize Google Drive service
            service = await self._get_drive_service()

            # Execute operation
            if self.operation == "upload":
                result = await self._upload_file(service, input_data)
            elif self.operation == "download":
                result = await self._download_file(service)
            elif self.operation == "list":
                result = await self._list_files(service, input_data)
            elif self.operation == "create_folder":
                result = await self._create_folder(service, input_data)
            elif self.operation == "delete":
                result = await self._delete_file(service)
            elif self.operation == "get_metadata":
                result = await self._get_file_metadata(service)
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "result": result
            }

        except Exception as e:
            logger.error(f"Google Drive operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation
            }

    async def _get_drive_service(self):
        """Initialize and return Google Drive service."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account

            # Load credentials
            creds = None

            if self.service_account_key:
                # Service account authentication
                creds = service_account.Credentials.from_service_account_info(
                    self.service_account_key,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            elif self.credentials_path:
                # OAuth2 credentials from file
                from google.oauth2.credentials import Credentials
                # This would require proper OAuth2 flow implementation
                raise NotImplementedError("OAuth2 flow not implemented")
            elif self.credentials_json:
                # Credentials from JSON string
                import json
                creds_data = json.loads(self.credentials_json)
                creds = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=['https://www.googleapis.com/auth/drive']
                )

            if not creds:
                raise ValueError("Could not load Google Drive credentials")

            # Build Drive service
            service = build('drive', 'v3', credentials=creds)
            return service

        except ImportError:
            raise RuntimeError("google-api-python-client and google-auth are required for Google Drive operations")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            raise

    async def _upload_file(self, service, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to Google Drive."""
        try:
            file_content = input_data.get("file_content", "")
            file_name = input_data.get("file_name", self.file_name) or "uploaded_file"
            mime_type = input_data.get("mime_type", self.mime_type) or "text/plain"

            # Prepare file metadata
            file_metadata = {
                'name': file_name,
                'mimeType': mime_type
            }

            if self.parent_folder_id:
                file_metadata['parents'] = [self.parent_folder_id]

            # Prepare file content
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            elif isinstance(file_content, dict):
                import json
                file_content = json.dumps(file_content).encode('utf-8')
                mime_type = "application/json"

            media = {
                'mimeType': mime_type,
                'body': io.BytesIO(file_content)
            }

            # Upload file
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,createdTime'
            ).execute()

            return {
                "file_id": file.get('id'),
                "file_name": file.get('name'),
                "web_view_link": file.get('webViewLink'),
                "created_time": file.get('createdTime'),
                "size": len(file_content)
            }

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise

    async def _download_file(self, service) -> Dict[str, Any]:
        """Download a file from Google Drive."""
        try:
            if not self.file_id:
                raise ValueError("file_id is required for download")

            # Get file metadata first
            file_metadata = service.files().get(fileId=self.file_id, fields='name,mimeType,size').execute()

            # Download file content
            request = service.files().get_media(fileId=self.file_id)
            file_content = io.BytesIO()
            downloader = request.execute()
            file_content.write(downloader)

            file_content.seek(0)
            content = file_content.read()

            # Try to decode as text, fallback to base64 for binary
            try:
                text_content = content.decode('utf-8')
                return {
                    "file_name": file_metadata.get('name'),
                    "content": text_content,
                    "mime_type": file_metadata.get('mimeType'),
                    "size": file_metadata.get('size'),
                    "encoding": "utf-8"
                }
            except UnicodeDecodeError:
                import base64
                return {
                    "file_name": file_metadata.get('name'),
                    "content": base64.b64encode(content).decode('utf-8'),
                    "mime_type": file_metadata.get('mimeType'),
                    "size": file_metadata.get('size'),
                    "encoding": "base64"
                }

        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise

    async def _list_files(self, service, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """List files in Google Drive."""
        try:
            query = input_data.get("query", "")
            page_size = input_data.get("page_size", 100)
            order_by = input_data.get("order_by", "modifiedTime desc")

            # Build query
            if self.parent_folder_id and not query:
                query = f"'{self.parent_folder_id}' in parents"
            elif self.parent_folder_id and query:
                query = f"'{self.parent_folder_id}' in parents and ({query})"

            # List files
            results = service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)",
                orderBy=order_by
            ).execute()

            files = results.get('files', [])
            next_page_token = results.get('nextPageToken')

            return {
                "files": files,
                "count": len(files),
                "next_page_token": next_page_token,
                "has_more": bool(next_page_token)
            }

        except Exception as e:
            logger.error(f"File listing failed: {e}")
            raise

    async def _create_folder(self, service, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder in Google Drive."""
        try:
            folder_name = input_data.get("folder_name", f"New Folder {datetime.now().strftime('%Y%m%d_%H%M%S')}")

            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if self.parent_folder_id:
                file_metadata['parents'] = [self.parent_folder_id]

            folder = service.files().create(
                body=file_metadata,
                fields='id,name,webViewLink,createdTime'
            ).execute()

            return {
                "folder_id": folder.get('id'),
                "folder_name": folder.get('name'),
                "web_view_link": folder.get('webViewLink'),
                "created_time": folder.get('createdTime')
            }

        except Exception as e:
            logger.error(f"Folder creation failed: {e}")
            raise

    async def _delete_file(self, service) -> Dict[str, Any]:
        """Delete a file from Google Drive."""
        try:
            if not self.file_id:
                raise ValueError("file_id is required for delete operation")

            service.files().delete(fileId=self.file_id).execute()

            return {
                "deleted": True,
                "file_id": self.file_id
            }

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            raise

    async def _get_file_metadata(self, service) -> Dict[str, Any]:
        """Get file metadata from Google Drive."""
        try:
            if not self.file_id:
                raise ValueError("file_id is required for metadata operation")

            file = service.files().get(
                fileId=self.file_id,
                fields='id,name,mimeType,modifiedTime,createdTime,size,webViewLink,owners,permissions'
            ).execute()

            return {
                "file_id": file.get('id'),
                "name": file.get('name'),
                "mime_type": file.get('mimeType'),
                "size": file.get('size'),
                "created_time": file.get('createdTime'),
                "modified_time": file.get('modifiedTime'),
                "web_view_link": file.get('webViewLink'),
                "owners": file.get('owners', []),
                "permissions": file.get('permissions', [])
            }

        except Exception as e:
            logger.error(f"Metadata retrieval failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Google Drive connection."""
        try:
            service = await self._get_drive_service()

            # Try to list files (should work if credentials are valid)
            results = service.files().list(pageSize=1, fields="files(id)").execute()
            return "files" in results

        except Exception as e:
            logger.error(f"Google Drive connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.operation == "upload":
            return {
                "type": "object",
                "properties": {
                    "file_content": {
                        "description": "Content of the file to upload"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file"
                    },
                    "mime_type": {
                        "type": "string",
                        "description": "MIME type of the file"
                    }
                },
                "required": ["file_content"]
            }
        elif self.operation == "list":
            return {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for files"
                    },
                    "page_size": {
                        "type": "integer",
                        "default": 100,
                        "description": "Number of files to return"
                    }
                }
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "operation": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation"]
        }
