# Rica Storage Layer — Local Backend
# Imports redirect to local implementations (SQLite + filesystem).
# Importing markdown_hooks installs the FTS5 auto-sync on the file client.

from storage.local_db import firestore_client
from storage.local_files import gcs_client
from storage.encryption import encryption
from storage.markdown_kb import markdown_kb
import storage.markdown_hooks  # noqa: F401  (side-effect: install patches)
