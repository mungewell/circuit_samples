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
    Const(b"\x03\x04\x0a\x00\x00\x00"),
    "unknown" / Byte,
    Const(b"\x00\x0e\x75\x9c\x53"),
    "unknown1" / Bytes(4),
    "len_blob" / Int32ul,
    "unknown2" / Bytes(4),
    "len_name" / Int32ul,
    "name" / PaddedString(this.len_name, "utf8"),
    "blob" / Bytes(this.len_blob),
)

PACK = Struct(
    "project_dir" / PK,
    "projects" / Array(64, PK),

    "sample_dir"/ PK,
    "samples" /Array(64, PK),

    "patch_dir" / PK,
    "patches" / Array(128, PK),

    "json" / PK,
)

#--------------------------------------------------
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

        # extract projects
        path = os.path.join(root, pack["project_dir"]["name"])
        os.mkdir(path)
        for i in range(len(pack["projects"])):
            if pack["projects"][i]["len_blob"]:
                # work around '/' and '\' issues
                name = os.path.join(path, pack["projects"][i]["name"] \
                        [len(pack["project_dir"]["name"]):])
                outfile = open(name, "wb")

                if outfile:
                    outfile.write(pack["projects"][i]["blob"])
                    outfile.close()

        # extract samples
        path = os.path.join(root, pack["sample_dir"]["name"])
        os.mkdir(path)
        for i in range(len(pack["samples"])):
            if pack["samples"][i]["len_blob"]:
                # work around '/' and '\' issues
                name = os.path.join(path, pack["samples"][i]["name"] \
                        [len(pack["sample_dir"]["name"]):])
                outfile = open(name, "wb")

                if outfile:
                    outfile.write(pack["samples"][i]["blob"])
                    outfile.close()

        # extract patchs
        path = os.path.join(root, pack["patch_dir"]["name"])
        os.mkdir(path)
        for i in range(len(pack["patches"])):
            if pack["patches"][i]["len_blob"]:
                # work around '/' and '\' issues
                name = os.path.join(path, pack["patches"][i]["name"] \
                        [len(pack["patch_dir"]["name"]):])
                outfile = open(name, "wb")

                if outfile:
                    outfile.write(pack["patches"][i]["blob"])
                    outfile.close()

        # extract json
        if pack["patches"][i]["len_blob"]:
            name = os.path.join(root, pack["json"]["name"])
            outfile = open(name, "wb")

            if outfile:
                outfile.write(pack["json"]["blob"])
                outfile.close()


if __name__ == "__main__":
    main()

