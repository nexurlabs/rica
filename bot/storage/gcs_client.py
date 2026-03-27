# Rica - File Storage Client Redirect
# This file redirects imports to the local filesystem implementation.
# Kept for backward compatibility with: from storage.gcs_client import gcs_client

from storage.local_files import gcs_client, LocalFileClient

__all__ = ["gcs_client", "LocalFileClient"]
