#!/usr/bin/python
#
# Script decode '.circuittrackspack' files
# (c) Simon Wood, 14 March 2022
#

# requires:
# https://github.com/construct/construct

from construct import *

PK = Struct(
    Const(b"PK"),
    "unknown" / Bytes(6),
    "type" / Byte,			# 0x08 = FILE
    "unknown1" / Bytes(9),

    "len_blob" / Int32ul,
    "unknown2" / Bytes(4),
    "len_name" / Int32ul,

    "group" / PaddedString(this._.len_name, "utf8"),
    "len_file" / Computed(this.len_name - this._.len_name),
    "name" / PaddedString(this.len_file, "utf8"),
    "blob" / Bytes(this.len_blob),

    "check" / Check(this.group == this._.name),	# check for 'json'
)

PKGRP = Struct(
    Const(b"PK"),
    "unknown" / Bytes(6),
    Const(b"\x00"),			# 0x00 = GROUP
    "unknown1" / Bytes(9),

    "len_blob" / Int32ul,
    "unknown2" / Bytes(4),
    "len_name" / Int32ul,

    "name" / PaddedString(this.len_name, "utf8"),
    "blob" / Bytes(this.len_blob),

    "files" / GreedyRange(PK),
)

PACK = Struct(
    "len_name" / Computed(0),
    "name" / Computed(""),

    "groups1" / GreedyRange(PKGRP),
    "json1" / PK,

)

#--------------------------------------------------

import zlib

def deflate(data, compresslevel=9):
    compress = zlib.compressobj(
            compresslevel,        # level: 0-9
            zlib.DEFLATED,        # method: must be DEFLATED
            -zlib.MAX_WBITS,      # window size in bits:
                                  #   -15..-8: negate, suppress header
                                  #   8..15: normal
                                  #   16..30: subtract 16, gzip header
            zlib.DEF_MEM_LEVEL,   # mem level: 1..8/9
            0                     # strategy:
                                  #   0 = Z_DEFAULT_STRATEGY
                                  #   1 = Z_FILTERED
                                  #   2 = Z_HUFFMAN_ONLY
                                  #   3 = Z_RLE
                                  #   4 = Z_FIXED
    )
    deflated = compress.compress(data)
    deflated += compress.flush()
    return deflated

def inflate(data):
    decompress = zlib.decompressobj(
            -zlib.MAX_WBITS  # see above
    )
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated

def main():
    import sys
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="tracks_pack.py")
    parser.add_argument('files', metavar='FILE', nargs=1,
        help='File to process')

    parser.add_argument("-d", "--dump",
        help="dump configuration to text",
        action="store_true", dest="dump")

    parser.add_argument("-u", "--unpack",
        help="unpack Projects/Samples/Patches to UNPACK directory",
        dest="unpack")

    options = parser.parse_args()

    if not len(options.files):
        parser.error("FILE not specified")

    # Read data from file
    infile = open(options.files[0], "rb")
    if not infile:
        sys.exit("Unable to open FILE for reading")
    else:
        data = infile.read()
    infile.close()

    if data:
        pack = PACK.parse(data)

        if options.dump:
            print(pack)

    if options.unpack and pack:
        root = os.path.join(os.getcwd(), options.unpack)
        if os.path.exists(root):
            sys.exit("Directory %s already exists" % root)

        os.mkdir(root)

        # extract files from groups
        for group in pack["groups1"]:
            path = os.path.join(root, group["name"])
            os.mkdir(path)
            for f in group["files"]:
                if f["len_blob"]:
                    name = os.path.join(path, f["name"])
                    outfile = open(name, "wb")

                    if outfile:
                        outfile.write(inflate(f["blob"]))
                        outfile.close()


        # extract json
        if pack["json1"]["len_blob"]:
            name = os.path.join(root, pack["json1"]["name"])
            outfile = open(name, "wb")

            if outfile:
                outfile.write(inflate(pack["json1"]["blob"]))
                outfile.close()


if __name__ == "__main__":
    main()

