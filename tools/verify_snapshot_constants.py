#!/usr/bin/env python3
"""Fail if the embedded V8 startup snapshot lacks any of the eight Math constants.

The five constants computed at genesis (E, LN2, LN10, LOG2E, LOG10E) can only be
produced by mksnapshot; every embedder starting from the default blob inherits
them. See supabase/edge-runtime#723.
"""
import struct
import sys

CONSTANTS = {
    "E": 2.718281828459045,
    "LN2": 0.6931471805599453,
    "LN10": 2.302585092994046,
    "LOG2E": 1.4426950408889634,
    "LOG10E": 0.4342944819032518,
    "PI": 3.141592653589793,
    "SQRT1_2": 0.7071067811865476,
    "SQRT2": 1.4142135623730951,
}


def members(data):
    """Yield (name, body) for GNU, BSD and MSVC `ar` archives."""
    assert data[:8] == b"!<arch>\n", "not an ar archive"
    off, longnames = 8, b""
    while off + 60 <= len(data):
        hdr = data[off:off + 60]
        name = hdr[:16].decode().rstrip()
        size = int(hdr[48:58])
        body = data[off + 60:off + 60 + size]
        if name == "//":
            longnames = body
        elif name.startswith("#1/"):                 # BSD: name is the first N bytes of body
            n = int(name[3:])
            yield body[:n].rstrip(b"\0").decode(), body[n:]
        elif name not in ("/", "/SYM64/"):
            if name.startswith("/"):                 # GNU / MSVC: index into the longname table
                i = int(name[1:])
                name = longnames[i:longnames.index(b"/\n", i)].decode()
            yield name.rstrip("/"), body
        off += 60 + size + (size & 1)


def main(path):
    data = open(path, "rb").read()
    snaps = [b for n, b in members(data) if n in ("snapshot.o", "snapshot.obj")]
    if not snaps:
        sys.exit(f"{path}: no snapshot object found")
    blob = max(snaps, key=len)                       # the generated one is the large one
    missing = [k for k, v in CONSTANTS.items() if struct.pack("<d", v) not in blob]
    if missing:
        sys.exit(f"{path}: embedded startup snapshot is missing Math constants: {', '.join(missing)}")
    print(f"{path}: all {len(CONSTANTS)} Math constants present in the embedded startup snapshot")


if __name__ == "__main__":
    main(sys.argv[1])
