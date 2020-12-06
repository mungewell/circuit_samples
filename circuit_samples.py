#!/usr/bin/python
#
# Script decode/encode manipulate Circuit's sample SysEx files
# (c) Simon Wood, 03 Dec 2020. GPLv2 or higher
#

from binascii import crc32

#--------------------------------------------------
# Define Sound data format using Construct (v2.9)
# requires:
# https://github.com/construct/construct

from construct import *

CircuitSample = Struct(
    "channels" / Byte,
    "bits" / Byte,
    "rate" / Int32ul,
    "length" / Int32ul,                 # in bytes
    "data" / Bytes(this.length),
)

CircuitSamples = Struct(
    "count" / Default(Byte, 0),
    "samples" / Default(Array(this.count, CircuitSample),[]),
)

#--------------------------------------------------
class circuit_samples(object):
    circuitHeader = (0x00, 0x20, 0x29, 0x00)
    maxLength = 0x0023B000

    length = 0x0023B000
    offset = 0x0057F000
    unpackedData = None
    checksum = 0

    def pack(self, data):
        # Pack 8bit data into 7bit
        # MSB's in first byte, followed by 7 bytes (bits 6..0).
        packet = bytearray(b"")
        encode = bytearray(b"\x00")

        for byte in data:
            encode[0] |= (byte & 0x80) >> (8 - len(encode))
            encode.append(byte & 0x7f)

            if len(encode) > 7:
                packet = packet + encode
                encode = bytearray(b"\x00")

        # don't forget the last few bytes
        if len(encode) > 1:
            packet = packet + encode

        return(packet)

    def unpack(self, packet):
        # Unpack data 7bit to 8bit
        # MSB's in first byte, followed by 7 bytes (bits 6..0).
        data = bytearray(b"")
        loop = 7
        hibits = 0

        for byte in packet:
            if loop < 7:
                if (hibits & (1 << loop)):
                    data.append(128 + byte)
                else:
                    data.append(byte)
                loop += 1
            else:
                hibits = byte
                loop = 0

        return(data)

    def packNyble(self, value):
        # Pack 32bit value into 8 bytes
        data = bytearray(b"")

        for nyble in reversed(range(8)):
            data.append((value >> (4 * nyble)) & 0x0f)

        return(data)

    def unpackNyble(self, data):
        # Unpack 8 bytes into 32bit value
        value = 0

        for nyble in range(8):
            value = value << 4
            value |= data[nyble] & 0x0f

        return(value)

    def readSysEx(self, filename):
        self.unpackedData = b""
        messages = mido.read_syx_file(filename)

        for msg in messages:
            if msg.type == 'sysex':
                header = msg.data[0:4]
                cmd = msg.data[4]
                if header == self.circuitHeader:
                    if cmd == 0x77:
                        self.length = self.unpackNyble(msg.data[5:13])
                        self.offset = self.unpackNyble(msg.data[13:21])
                    if cmd == 0x79:
                        self.unpackedData += self.unpack(bytes(msg.data[5:]))
                    if cmd == 0x7a:
                        self.checksum = self.unpackNyble(msg.data[5:13])

        return(self.unpackedData)

    def writeSysEx(self, filename, unpackedData):
        messages = []

        # need to figure out whether we must pad the bytes
        self.length = len(unpackedData)
        self.unpackedData = unpackedData
        self.checksum = crc32(unpackedData)

        data = bytes(self.circuitHeader) + b"\x77" + \
                self.packNyble(self.length) + \
                self.packNyble(self.offset)
        messages.append(mido.Message('sysex', data=data))

        while unpackedData:
            # chunk into 256 bytes
            data = bytes(self.circuitHeader) + b"\x79" + \
                    self.pack(unpackedData[0:256])
            unpackedData = unpackedData[256:]
            messages.append(mido.Message('sysex', data=data))

        data = bytes(self.circuitHeader) + b"\x7a" + \
                self.packNyble(self.checksum)
        messages.append(mido.Message('sysex', data=data))

        '''
        for msg in messages:
            if msg.type == 'sysex':
                print(msg)
        '''
        mido.write_syx_file(filename, messages, plaintext=False)

    def endianSwap(self, data, width):
        raw = bytearray()
        if width == 4:
            for i in range(0, len(data), width):
                    a = data[i:i+width]
                    raw.append(a[3])
                    raw.append(a[2])
                    raw.append(a[1])
                    raw.append(a[0])
        elif width == 3:
            for i in range(0, len(data), width):
                    a = data[i:i+width]
                    raw.append(a[2])
                    raw.append(a[1])
                    raw.append(a[0])
        elif width == 2:
            for i in range(0, len(data), width):
                    a = data[i:i+width]
                    raw.append(a[1])
                    raw.append(a[0])
        else:
            return(data)

        return(bytes(raw))

#--------------------------------------------------

if __name__ == "__main__":
    import sys
    import os
    import wave
    import struct

    from optparse import OptionParser

    try:
        import mido
        _hasMido = True
        if sys.platform == 'win32':
            mido.set_backend('mido.backends.rtmidi_python')
    except ImportError:
        _hasMido = False
    '''
    _hasMido = False
    '''

    usage = "usage: %prog [options] FILENAME"
    parser = OptionParser(usage)

    parser.add_option("-v", "--verbose",
        action="store_true", dest="verbose")
    parser.add_option("-i", "--info",
        help="summarize Samples/SysEx in human readable form",
        action="store_true", dest="info")
    parser.add_option("-o", "--outfile",
        help="store SysEx into OUTFILE",
        dest="outfile")
    parser.add_option("-O", "--samefile",
        help="store SysEx into same file as input",
        action="store_true", dest="samefile")
    parser.add_option("-n", "--nopad",
        help="do not pad resultant SysEx upto max size (experimental)",
        action="store_true", dest="nopad")

    parser.add_option("-u", "--unpack",
        help="unpack Samples/SysEx to UNPACK directory",
        dest="unpack")
    parser.add_option("-p", "--pack",
        help="pack PACK directory of samples to SysEx (overwrites contents)",
        dest="pack")

    '''
    parser.add_option("-d", "--del",
        help="delete sample number DEL (changes numbering of others)",
        dest="del")
    '''
    parser.add_option("-a", "--add",
        help="add file 'ADD.wav' (at end, or replacing SAMPLE number)",
        dest="add")
    parser.add_option("-s", "--sample", type="int",
        help="export/replace SAMPLE number",
        dest="sample", default=64)
    parser.add_option("-x", "--export",
        help="export SAMPLE number as file 'EXPORT.wav'",
        dest="export")

    parser.add_option("-R", "--raw",
        help="use '.raw' sample files (rather than '.wav')",
        action="store_true", dest="raw")
    parser.add_option("-F", "--force",
        help="force rate/ch/bit when importing '.wav'",
        action="store_true", dest="force")
    parser.add_option("-r", "--rate", type="int",
        help="set RATE when importing '.raw' files",
        dest="rate", default=48000)
    parser.add_option("-c", "--ch", type="int",
        help="set CH(annels) when importing '.raw' files",
        dest="ch", default=1)
    parser.add_option("-b", "--bits", type="int",
        help="set BITS when importing '.raw' files",
        dest="bits", default=16)

    (options, args) = parser.parse_args()
    # print(options)

    circuit = circuit_samples()
    samples = None

    if len(args) == 1:
        sampleData = circuit.readSysEx(args[0])

        if sampleData:
            samples = CircuitSamples.parse(sampleData)

        if options.samefile:
            options.outfile = args[0]

    if options.unpack and samples:
        path = os.path.join(os.getcwd(), options.unpack)
        if os.path.exists(path):
            sys.exit("Directory %s already exists" % path)

        os.mkdir(path)

        count = 1
        for sample in samples['samples']:
            if options.verbose:
                print("Unpacking sample %d : %s" % (count, path))

            if options.raw:
                name = os.path.join(path, "sample_{0:0=2d}.raw".format(count))
                outfile = open(name, "wb")
                outfile.write(sample['data'])
                outfile.close()

                # playback: aplay -c 1 -f S16_BE -r 48000 test/sample_01.raw
            else:
                name = os.path.join(path, "sample_{0:0=2d}.wav".format(count))
                outfile = wave.open(name, "wb")

                width = int(sample['bits'] / 8)
                outfile.setsampwidth(width)
                outfile.setnchannels(sample['channels'])
                outfile.setframerate(sample['rate'])

                # problem... sample data is BigEndian :-(
                if width > 1:
                    outfile.writeframesraw(circuit.endianSwap(
                            sample['data'], width))
                else:
                    outfile.writeframesraw(sample['data'])
                outfile.close()
            count += 1

    if options.export and samples:
            if options.sample > len(samples['samples']):
                sys.exit("Sample %d does not exist" % options.sample)

            if options.verbose:
                print("Unpacking Sample %d to %s" % (options.sample, options.export))

            sample = samples['samples'][options.sample - 1]
            if options.raw:
                # subsitute suffix if needed
                if options.export[-4:] == '.wav':
                    options.export = options.export[:-4] + '.raw'
            
                name = os.path.join(os.getcwd(), "%s" % options.export)
                outfile = open(name, "wb")
                outfile.write(sample['data'])
                outfile.close()

                # playback: aplay -c 1 -f S16_BE -r 48000 test/sample_01.raw
            else:
                name = os.path.join(os.getcwd(), "%s" % options.export)
                outfile = wave.open(name, "wb")

                width = int(sample['bits'] / 8)
                outfile.setsampwidth(width)
                outfile.setnchannels(sample['channels'])
                outfile.setframerate(sample['rate'])

                # problem... sample data is BigEndian :-(
                if width > 1:
                    outfile.writeframesraw(circuit.endianSwap(
                            sample['data'], width))
                else:
                    outfile.writeframesraw(sample['data'])
                outfile.close()

    # need to create an empty SysEx if it doesn't exist
    if not samples:
        temp = CircuitSamples.build({})
        samples = CircuitSamples.parse(temp)

    if options.pack and samples:
        path = os.path.join(os.getcwd(), options.pack)

        for count in range(1,65):
            if options.verbose:
                print("Packing sample %d : %s" % (count, path))

            if options.raw:
                name = os.path.join(path, "sample_{0:0=2d}.raw".format(count))
            else:
                name = os.path.join(path, "sample_{0:0=2d}.wav".format(count))

            infile = None
            if os.path.isfile(name):
                infile = wave.open(name, "rb")

            if infile:
                if infile.getsampwidth() > 1:
                    raw = circuit.endianSwap(infile.readframes(
                        infile.getnframes()), infile.getsampwidth())
                else:
                    raw = infile.readframes(infile.getnframes())

                if options.force or options.raw:
                    samples['samples'].append({
                        "channels": options.ch,
                        "bits": options.bits,
                        "rate": options.rate,
                        "length": len(raw),
                        "data": raw })
                else:
                    samples['samples'].append({
                        "channels": infile.getnchannels(),
                        "bits": 8 * infile.getsampwidth(),
                        "rate": infile.getframerate(),
                        "length": len(raw),
                        "data": raw })

                samples['count'] = count
            else:
                break

    if options.add and samples:
        if options.sample < 1:
            options.sample = 64

        if options.sample > samples['count']:
            # add at end
            count = samples['count']
        else:
            # replace sample
            count = options.sample - 1

        if True:
            if options.raw:
                # subsitute suffix if needed
                if options.add[-4:] == '.wav':
                    options.add = options.add[:-4] + '.raw'

            name = os.path.join(os.getcwd(), options.add)
            if not os.path.isfile(name):
                sys.exit("Unable to open file %s for reading", name)

            if options.verbose:
                print("Adding sample %d : %s" % (count + 1, name))

            if options.raw:
                infile = open(name, "rb")
                if infile:
                    raw = infile.read()
            else:
                infile = wave.open(name, "rb")
                if infile:
                    if infile.getsampwidth() > 1:
                        raw = circuit.endianSwap(infile.readframes(
                            infile.getnframes()), infile.getsampwidth())
                    else:
                        raw = infile.readframes(infile.getnframes())

            if options.force or options.raw:
                samples['samples'].append({
                    "channels": options.ch,
                    "bits": options.bits,
                    "rate": options.rate,
                    "length": len(raw),
                    "data": raw })
            else:
                samples['samples'].append({
                    "channels": infile.getnchannels(),
                    "bits": 8 * infile.getsampwidth(),
                    "rate": infile.getframerate(),
                    "length": len(raw),
                    "data": raw })

            samples['count'] = samples['count']+1

    if options.info and samples:
        count = 1
        print("Number of samples:", samples['count'])
        for sample in samples['samples']:
            print("Sample %d: %d bytes (%f seconds, %d ch %d bits @ %d)" %
                    (count, sample['length'],
                    sample['length'] * 8 / (sample['bits'] * sample['rate']),
                    sample['channels'], sample['bits'], sample['rate']))
            count += 1

    if options.outfile and samples:
        sampleData = CircuitSamples.build(samples)

        # by default we pad the file upto the maximum size
        if not options.nopad and len(sampleData) < circuit.maxLength:
            sampleData += b"\x00" * (circuit.maxLength - len(sampleData))

        if len(sampleData) > circuit.maxLength:
            sys.exit("Resultant SysEx too large for Circuit")

        if options.verbose:
            print("Creating SysEx file %s" % options.outfile)

        circuit.writeSysEx(options.outfile, sampleData)


