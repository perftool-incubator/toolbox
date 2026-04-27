import lzma
import os


def open_write_text_file(filename):
    """Open a file for writing with automatic xz compression.

    If the filename doesn't already end in '.xz', '.xz' is appended.
    Returns the opened file handle (text mode) and the actual filename used.
    """
    if not filename.endswith(".xz"):
        filename += ".xz"
    return lzma.open(filename, "wt"), filename


def open_read_text_file(filename):
    """Open a file for reading with transparent xz decompression.

    If filename.xz exists, it is preferred over the uncompressed version.
    Returns the opened file handle (text mode) and the actual filename used.
    """
    xz_filename = filename + ".xz"
    if os.path.exists(xz_filename):
        return lzma.open(xz_filename, "rt"), xz_filename
    if os.path.exists(filename):
        if filename.endswith(".xz"):
            return lzma.open(filename, "rt"), filename
        return open(filename, "r"), filename
    raise FileNotFoundError(f"Neither {filename} nor {xz_filename} found")
