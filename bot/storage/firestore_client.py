# Rica — Storage Client Redirect (Backward Compatibility Shim)
# ════════════════════════════════════════════════════════════
# This file exists ONLY for backward compatibility.
# Rica was originally built on Google Cloud Firestore. When it was
# decoupled to local-first SQLite storage, imports like:
#
#     from storage.firestore_client import firestore_client
#
# were kept working by redirecting to the new local_db module.
# New code should import directly from storage.local_db instead.
# ════════════════════════════════════════════════════════════

from storage.local_db import firestore_client, LocalDB

__all__ = ["firestore_client", "LocalDB"]
