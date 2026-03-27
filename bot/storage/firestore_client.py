# Rica - Storage Client Redirect
# This file redirects imports to the local SQLite implementation.
# Kept for backward compatibility with: from storage.firestore_client import firestore_client

from storage.local_db import firestore_client, LocalDB

__all__ = ["firestore_client", "LocalDB"]
