import subprocess

# pip install pip install pyelftools
from elftools.elf.elffile import ELFFile, SymbolTableSection

from config import ABS_PATH

# "c++filt" or "llvm-cxxfilt", whichever you have installer
DEMANGLER = "llvm-cxxfilt"

# if CreateProcess throws an exception, lower this value
SYM_STEP = 100

def demangle(symbols: list):
    demangled = []
    for i in range(0, len(symbols), 100):
        args = [DEMANGLER]
        args.extend(symbols[i:i + 100])
        pipe = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, _ = pipe.communicate()
        tmp = stdout.split("\n".encode())[:-1]
        demangled.extend(tmp)
    return demangled

def dump_symbols(filename):
    symlist = []

    # open binary
    with open(filename, 'rb') as f:
        elffile = ELFFile(f)

        # find symbol section
        for section in elffile.iter_sections():
            if isinstance(section, SymbolTableSection):
                addresses = []
                symbols = []

                # dump symbols
                for sym in section.iter_symbols():
                    if sym.name != '':
                        addr = int(sym.entry['st_value'])
                        addresses.append(addr)
                        symbols.append(sym.name)

                # demangle symbols
                demangled = demangle(symbols)

                # save symbols
                assert len(addresses) == len(demangled)
                for i in range(len(symbols)):
                    dtorPrefix = ""
                    dem = demangled[i].decode()
                    if dem.find("~") != -1:
                        if symbols[i].find("D0") != -1:
                            dtorPrefix = "/* Deleting Dtor */ "
                        if symbols[i].find("D1") != -1:
                            dtorPrefix = "/* Complete Dtor */ "
                        if symbols[i].find("D2") != -1:
                            dtorPrefix = "/* Base Dtor */ "
                    symlist.append(f'{dtorPrefix}{demangled[i].decode()} = {hex(addresses[i])}')                        

    # sort alphabetically
    symlist.sort()
    return symlist

symlist = dump_symbols(ABS_PATH + "binary.so")
with open(ABS_PATH + "symbols.txt", 'w') as f:
    for line in symlist:
        f.write(line + '\n')
    f.close()

print("Symbols dumped")