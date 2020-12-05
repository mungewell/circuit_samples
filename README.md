# circuit_samples

Small Python script to process the SysEx file containing samples uploaded
to the Novation Circuit.

Script allows for packing/unpacking samples en-mass and individually.
There are also some experiment features for testing the actual/non-official
capabilities of the Circuit.

Most simple usage would be to unpack all samples:
```
$ python3 circuit_samples.py -u unpacked/ samples.sysex
```

NOTE: *NOT TESTED ON REAL CIRCUIT AT THIS TIME.*

```
$ python3 circuit_samples.py -h
Usage: circuit_samples.py [options] FILENAME

Options:
  -h, --help            show this help message and exit
  -v, --verbose         
  -i, --info            summarize Samples/SysEx in human readable form
  -o OUTFILE, --outfile=OUTFILE
                        store SysEx into OUTFILE
  -O, --samefile        store SysEx into same file as input
  -n, --nopad           do not pad resultant SysEx upto max size
                        (experimental)
  -u UNPACK, --unpack=UNPACK
                        unpack Samples/SysEx to UNPACK directory
  -p PACK, --pack=PACK  pack PACK directory of samples to SysEx (overwrites
                        contents)
  -a ADD, --add=ADD     add file 'ADD.wav' (at end, or replacing SAMPLE
                        number)
  -s SAMPLE, --sample=SAMPLE
                        export/replace SAMPLE number
  -x EXPORT, --export=EXPORT
                        export SAMPLE number as file 'EXPORT.wav'
  -R, --raw             use '.raw' sample files (rather than '.wav')
  -F, --force           force rate/ch/bit when importing '.wav'
  -r RATE, --rate=RATE  set RATE when importing '.raw' files
  -c CH, --ch=CH        set CH(annels) when importing '.raw' files
  -b BITS, --bits=BITS  set BITS when importing '.raw' files
```
