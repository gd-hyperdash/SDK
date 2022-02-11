# pip install pip install pyelftools
from elftools.elf.elffile import ELFFile

from config import ABS_PATH, VTABLE_PATH, THUMB_MODE

# open binary
with open(ABS_PATH + "binary.so", "rb") as elfh:
    elf = ELFFile(elfh)

    # find code section
    text_sec = elf.get_section_by_name(".text")
    text_start = int(text_sec.header['sh_addr'])
    text_end = text_start + int(text_sec.header['sh_size'])

    # open symbols list
    with open(ABS_PATH + "symbols.txt", 'r') as f:
        symlist = f.read().split('\n')
        for line in symlist:
            vtable = []

            # look for vtables
            if line.startswith("vtable for "):
                line = line.replace("vtable for ", "")

                # get vtable name
                vtname = line.split(" = ")[0]
                vtname = vtname.replace(':', '_')

                # get vtable address
                vtaddr = int(line.split(" = ")[1], base=16)

                # seek to vtable address, skip first two
                # first is null, second is typeinfo pointer
                elfh.seek(vtaddr + 8)
                while True:
                    # read next vtable entry, until we find an unvalid one
                    entry_addr = int.from_bytes(elfh.read(4), byteorder='little') & (0xFFFFFFFF - int(THUMB_MODE))
                    if entry_addr < text_start or entry_addr > text_end:
                        break
                    vtable.append(entry_addr)

                # attempt to save the vtable
                try:
                    with open(VTABLE_PATH + vtname + ".vt", 'w') as vth:
                        for vtentry in vtable:
                            vth.write(hex(vtentry) + '\n')
                        vth.close()
                except:
                    print(f"WARNING: could not dump vtable for '{vtname}'")

        f.close()
    elfh.close()