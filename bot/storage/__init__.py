# Rica Storage Layer — Local Backend
# Imports redirect to local implementations (SQLite + filesystem)

from storage.local_db import firestore_client
from storage.local_files import gcs_client
from storage.encryption import encryption
