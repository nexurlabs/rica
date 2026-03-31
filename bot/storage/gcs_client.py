# Rica — File Storage Client Redirect (Backward Compatibility Shim)
# ════════════════════════════════════════════════════════════
# This file exists ONLY for backward compatibility.
# Rica was originally built on Google Cloud Storage (GCS). When it was
# decoupled to local-first file storage, imports like:
#
#     from storage.gcs_client import gcs_client
#
# were kept working by redirecting to the new local_files module.
# New code should import directly from storage.local_files instead.
# ════════════════════════════════════════════════════════════

from storage.local_files import gcs_client, LocalFileClient

__all__ = ["gcs_client", "LocalFileClient"]
