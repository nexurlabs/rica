# Rica - Markdown KB Auto-Sync Hooks
# Wraps the LocalFileClient methods so any markdown write/delete/update
# auto-updates the FTS5 index. Import this module to install the hooks.
#
# Patching is done with captured originals to avoid recursion: the wrapper
# calls the original implementation, which lives in a separate
# `_LocalFileClientBase` (mixed in before the patch) so the call never
# re-enters our wrapper.

from storage.local_files import LocalFileClient
from storage.markdown_kb import markdown_kb


_MARKDOWN_SUFFIXES = (".md", ".markdown", ".txt")


def _is_indexable(file_path: str) -> bool:
    return file_path.endswith(_MARKDOWN_SUFFIXES)


def _install_patches():
    """Install instrumented wrappers on LocalFileClient, capturing the
    real originals on first call (one-time, idempotent).
    """
    if getattr(LocalFileClient, "_kb_patched", False):
        return

    # Step 1: rename the real methods to private aliases. These are the
    # ones our wrappers will call, so we never recurse.
    LocalFileClient._kb_write_file = LocalFileClient.write_file
    LocalFileClient._kb_append_file = LocalFileClient.append_file
    LocalFileClient._kb_delete_file = LocalFileClient.delete_file
    LocalFileClient._kb_delete_folder = LocalFileClient.delete_folder

    def write_file(self, server_id, file_path, content):
        self._kb_write_file(server_id, file_path, content)
        if _is_indexable(file_path):
            markdown_kb.index(server_id, file_path, content)

    def append_file(self, server_id, file_path, content):
        self._kb_append_file(server_id, file_path, content)
        if _is_indexable(file_path):
            full = self.read_file(server_id, file_path) or ""
            markdown_kb.index(server_id, file_path, full)

    def delete_file(self, server_id, file_path):
        self._kb_delete_file(server_id, file_path)
        if _is_indexable(file_path):
            markdown_kb.remove(server_id, file_path)

    def delete_folder(self, server_id, prefix):
        self._kb_delete_folder(server_id, prefix)
        removed = markdown_kb.remove_prefix(server_id, prefix)
        if removed:
            print(f"[MarkdownKB] removed {removed} indexed file(s) under {prefix}/")

    LocalFileClient.write_file = write_file
    LocalFileClient.append_file = append_file
    LocalFileClient.delete_file = delete_file
    LocalFileClient.delete_folder = delete_folder
    LocalFileClient._kb_patched = True


_install_patches()
