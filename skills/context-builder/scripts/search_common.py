"""Shared validation and cache fingerprints for the reading-list scripts."""

import hashlib
import os


def tree_stamp(files, version):
    """Detect renames, removals, and edits even below the tree's newest mtime.

    Metadata keeps warm searches cheap. ctime also catches rewrites that preserve
    size and mtime; this is a local cache fingerprint, not a content checksum.
    """
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(os.fsencode(path) + b"\0")
        try:
            stat = os.stat(path)
            metadata = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        except OSError:
            metadata = None
        digest.update(repr(metadata).encode() + b"\0")
    return {"version": version, "files": len(files), "digest": digest.hexdigest()}


def validate_options(parser, args):
    if args.n < 0:
        parser.error("-n must be zero or greater")
    if args.seeds < 1:
        parser.error("--seeds must be at least 1")
    if not 0 <= args.fuzzy <= 1:
        parser.error("--fuzzy must be between 0 and 1")
