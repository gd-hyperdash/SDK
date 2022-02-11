# pip install pip install pyelftools
from elftools.elf.elffile import ELFFile

from config import ABS_PATH, THUMB_MODE

typeinfos = []

def find_entry_name(addr: int):
    for ty in typeinfos:
        if addr == ty[1]:
            return ty[0]
    
    return ""

output = open(ABS_PATH + "typeinfos.txt", 'w')

# open symbols
with open(ABS_PATH + "symbols.txt", 'r') as f:
    symlist = f.read().split('\n')

    # look for typeinfos
    for line in symlist:
        if line.startswith("typeinfo for "):
            line = line.replace("typeinfo for ", "")

            # get typeinfo name
            typename = line.split(" = ")[0]

            # get typeinfo address
            typeaddr = int(line.split(" = ")[1], base=16)

            # add to global list
            typeinfos.append([typename, typeaddr])

    f.close()

# open binary
with open(ABS_PATH + "binary.so", "rb") as elfh:
    elf = ELFFile(elfh)

    # find data section
    data_sec = elf.get_section_by_name(".data.rel.ro")
    data_start = int(data_sec.header['sh_addr'])
    data_end = data_start + int(data_sec.header['sh_size'])

    # Handle typeinfos
    for ty in typeinfos:
        tyentries = []
        tyname = ty[0]
        tyaddr = ty[1]

        # get to typeinfo, skip two
        # first is some offset, second is typeinfo name
        elfh.seek(tyaddr + 8)

        entry_addr = int.from_bytes(elfh.read(4), byteorder='little') & (0xFFFFFFFF - int(THUMB_MODE))

        # if attributes is zero, we are given a number of base classes
        if (entry_addr == 0):
            num_of_entries = int.from_bytes(elfh.read(4), byteorder='little')

            # unreasonable enough for both inheritance (too big) and addresses (too low)
            if num_of_entries < 128:
                while num_of_entries > 0:
                    if entry_addr >= data_start and entry_addr < data_end:
                        entry_name = find_entry_name(entry_addr)
                        if entry_name != "":
                            tyentries.append(entry_name)
                            #  skip attributes
                            elfh.seek(4, 1)
                            num_of_entries -= 1

                    entry_addr = int.from_bytes(elfh.read(4), byteorder='little') & (0xFFFFFFFF - int(THUMB_MODE))

        else: # read next typeinfo entry, until we find an unvalid one
            while True:
                if entry_addr < data_start or entry_addr > data_end:
                    break

                entry_name = find_entry_name(entry_addr)

                if entry_name == "":
                    break

                # TODO: find access
                tyentries.append(entry_name)
                entry_addr = int.from_bytes(elfh.read(4), byteorder='little') & (0xFFFFFFFF - int(THUMB_MODE))

        # write typeinfo
        output.write(tyname)

        for entry in tyentries:
            output.write("|" + entry)

        output.write('\n')

output.close()