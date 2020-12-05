from cx_Freeze import setup, Executable

base = None    

executables = [Executable("circuit_samples.py", base=base)]

packages = ["construct", "os", "optparse", "sys", "binascii", "mido", "rtmidi_python"]
options = {
    'build_exe': {    
        'packages':packages,
        'excludes':["pygame", "numpy"],
    },    
}

setup(
    name = "circuit_samples.py",
    options = options,
    version = "0.1.0.0",
    description = "Library for Sample SysEx files for Novation Circuit",
    executables = executables
)
