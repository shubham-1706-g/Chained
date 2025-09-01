"""S3 Upload Storage Action

This module implements an action for uploading files to Amazon S3.
It can upload, download, list, and manage files in S3 buckets.
"""

import logging
import io
import json
from typing import Any, Dict, Optional, List
from datetime import datetime

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class S3UploadAction(BaseAction):
    """Action for Amazon S3 file operations.

    This action supports:
    - File upload to S3 buckets
    - File download from S3 buckets
    - File listing and searching
    - File deletion
    - Presigned URL generation
    - Bucket operations
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.operation = config.get("operation", "upload")  # upload, download, list, delete, get_url
        self.bucket_name = config.get("bucket_name", "")
        self.region = config.get("region", "us-east-1")
        self.access_key_id = config.get("access_key_id", "")
        self.secret_access_key = config.get("secret_access_key", "")
        self.session_token = config.get("session_token", "")  # For temporary credentials
        self.file_key = config.get("file_key", "")  # S3 object key
        self.file_name = config.get("file_name", "")
        self.content_type = config.get("content_type", "")
        self.acl = config.get("acl", "private")  # private, public-read, etc.
        self.metadata = config.get("metadata", {})
        self.tags = config.get("tags", {})
        self.expiration = config.get("expiration", 3600)  # For presigned URLs

    async def validate_config(self) -> bool:
        """Validate S3 action configuration."""
        if not self.bucket_name:
            raise ValueError("bucket_name is required for S3 operations")

        if not all([self.access_key_id, self.secret_access_key]):
            raise ValueError("access_key_id and secret_access_key are required")

        valid_operations = ["upload", "download", "list", "delete", "get_url", "copy", "move"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        if self.operation in ["upload", "download"] and not self.file_key:
            raise ValueError("file_key is required for upload/download operations")

        valid_acls = ["private", "public-read", "public-read-write", "authenticated-read", "bucket-owner-read", "bucket-owner-full-control"]
        if self.acl not in valid_acls:
            raise ValueError(f"Invalid ACL: {self.acl}. Must be one of {valid_acls}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the S3 operation."""
        try:
            # Initialize S3 client
            s3_client = await self._get_s3_client()

            # Execute operation
            if self.operation == "upload":
                result = await self._upload_file(s3_client, input_data)
            elif self.operation == "download":
                result = await self._download_file(s3_client)
            elif self.operation == "list":
                result = await self._list_files(s3_client, input_data)
            elif self.operation == "delete":
                result = await self._delete_file(s3_client)
            elif self.operation == "get_url":
                result = await self._get_presigned_url(s3_client)
            elif self.operation == "copy":
                result = await self._copy_file(s3_client, input_data)
            elif self.operation == "move":
                result = await self._move_file(s3_client, input_data)
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "bucket": self.bucket_name,
                "result": result
            }

        except Exception as e:
            logger.error(f"S3 operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation,
                "bucket": self.bucket_name
            }

    async def _get_s3_client(self):
        """Initialize and return S3 client."""
        try:
            import boto3
            from botocore.config import Config

            # Prepare AWS credentials
            aws_config = {
                'aws_access_key_id': self.access_key_id,
                'aws_secret_access_key': self.secret_access_key,
                'region_name': self.region
            }

            if self.session_token:
                aws_config['aws_session_token'] = self.session_token

            # Create S3 client with retry configuration
            config = Config(
                retries={
                    'max_attempts': 3,
                    'mode': 'standard'
                }
            )

            s3_client = boto3.client('s3', **aws_config, config=config)
            return s3_client

        except ImportError:
            raise RuntimeError("boto3 is required for S3 operations")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    async def _upload_file(self, s3_client, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to S3."""
        try:
            file_content = input_data.get("file_content", "")
            file_key = input_data.get("file_key", self.file_key) or f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            content_type = input_data.get("content_type", self.content_type) or "text/plain"
            metadata = input_data.get("metadata", self.metadata)
            tags = input_data.get("tags", self.tags)

            # Prepare file content
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            elif isinstance(file_content, dict):
                file_content = json.dumps(file_content).encode('utf-8')
                if not content_type or content_type == "text/plain":
                    content_type = "application/json"

            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': file_key,
                'Body': file_content,
                'ContentType': content_type,
                'ACL': self.acl
            }

            if metadata:
                upload_params['Metadata'] = {k: str(v) for k, v in metadata.items()}

            if tags:
                tag_string = '&'.join([f"{k}={v}" for k, v in tags.items()])
                upload_params['Tagging'] = tag_string

            # Upload file
            response = s3_client.put_object(**upload_params)

            return {
                "file_key": file_key,
                "bucket": self.bucket_name,
                "etag": response.get('ETag', '').strip('"'),
                "version_id": response.get('VersionId'),
                "size": len(file_content),
                "content_type": content_type,
                "last_modified": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    async def _download_file(self, s3_client) -> Dict[str, Any]:
        """Download a file from S3."""
        try:
            if not self.file_key:
                raise ValueError("file_key is required for download")

            # Download file
            response = s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.file_key
            )

            file_content = response['Body'].read()

            # Try to decode as text, fallback to base64 for binary
            content_type = response.get('ContentType', 'application/octet-stream')
            try:
                if content_type.startswith('text/') or content_type == 'application/json':
                    text_content = file_content.decode('utf-8')
                    return {
                        "file_key": self.file_key,
                        "content": text_content,
                        "content_type": content_type,
                        "size": len(file_content),
                        "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                        "etag": response.get('ETag', '').strip('"'),
                        "encoding": "utf-8"
                    }
                else:
                    import base64
                    return {
                        "file_key": self.file_key,
                        "content": base64.b64encode(file_content).decode('utf-8'),
                        "content_type": content_type,
                        "size": len(file_content),
                        "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                        "etag": response.get('ETag', '').strip('"'),
                        "encoding": "base64"
                    }
            except UnicodeDecodeError:
                import base64
                return {
                    "file_key": self.file_key,
                    "content": base64.b64encode(file_content).decode('utf-8'),
                    "content_type": content_type,
                    "size": len(file_content),
                    "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                    "etag": response.get('ETag', '').strip('"'),
                    "encoding": "base64"
                }

        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            raise

    async def _list_files(self, s3_client, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """List files in S3 bucket."""
        try:
            prefix = input_data.get("prefix", "")
            max_keys = input_data.get("max_keys", 1000)
            continuation_token = input_data.get("continuation_token")

            # List objects
            list_params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }

            if prefix:
                list_params['Prefix'] = prefix

            if continuation_token:
                list_params['ContinuationToken'] = continuation_token

            response = s3_client.list_objects_v2(**list_params)

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "etag": obj['ETag'].strip('"'),
                        "storage_class": obj.get('StorageClass', 'STANDARD')
                    })

            return {
                "files": files,
                "count": len(files),
                "is_truncated": response.get('IsTruncated', False),
                "continuation_token": response.get('NextContinuationToken'),
                "prefix": prefix
            }

        except Exception as e:
            logger.error(f"S3 list failed: {e}")
            raise

    async def _delete_file(self, s3_client) -> Dict[str, Any]:
        """Delete a file from S3."""
        try:
            if not self.file_key:
                raise ValueError("file_key is required for delete")

            response = s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=self.file_key
            )

            return {
                "deleted": True,
                "file_key": self.file_key,
                "bucket": self.bucket_name,
                "delete_marker": response.get('DeleteMarker', False),
                "version_id": response.get('VersionId')
            }

        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            raise

    async def _get_presigned_url(self, s3_client) -> Dict[str, Any]:
        """Generate a presigned URL for S3 file access."""
        try:
            if not self.file_key:
                raise ValueError("file_key is required for presigned URL")

            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': self.file_key
                },
                ExpiresIn=self.expiration
            )

            return {
                "url": url,
                "file_key": self.file_key,
                "bucket": self.bucket_name,
                "expires_in": self.expiration,
                "expires_at": (datetime.utcnow().timestamp() + self.expiration)
            }

        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise

    async def _copy_file(self, s3_client, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Copy a file within S3."""
        try:
            source_key = input_data.get("source_key", self.file_key)
            destination_key = input_data.get("destination_key", "")

            if not source_key or not destination_key:
                raise ValueError("source_key and destination_key are required for copy")

            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }

            response = s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_key
            )

            return {
                "copied": True,
                "source_key": source_key,
                "destination_key": destination_key,
                "bucket": self.bucket_name,
                "etag": response.get('CopyObjectResult', {}).get('ETag', '').strip('"'),
                "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None
            }

        except Exception as e:
            logger.error(f"S3 copy failed: {e}")
            raise

    async def _move_file(self, s3_client, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Move a file within S3 (copy then delete)."""
        try:
            # First copy the file
            copy_result = await self._copy_file(s3_client, input_data)

            # Then delete the original
            original_key = self.file_key
            self.file_key = input_data.get("source_key", self.file_key)
            delete_result = await self._delete_file(s3_client)

            return {
                "moved": True,
                "source_key": original_key,
                "destination_key": copy_result["destination_key"],
                "bucket": self.bucket_name
            }

        except Exception as e:
            logger.error(f"S3 move failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test S3 connection."""
        try:
            s3_client = await self._get_s3_client()

            # Try to list objects (should work if credentials are valid)
            response = s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )

            return True

        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
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
                    "file_key": {
                        "type": "string",
                        "description": "S3 object key for the file"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "MIME type of the file"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadata to attach to the file"
                    },
                    "tags": {
                        "type": "object",
                        "description": "Tags to attach to the file"
                    }
                },
                "required": ["file_content"]
            }
        elif self.operation == "list":
            return {
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "Prefix to filter objects"
                    },
                    "max_keys": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Maximum number of objects to return"
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
                "bucket": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation", "bucket"]
        }
