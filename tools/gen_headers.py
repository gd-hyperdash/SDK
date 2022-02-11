from config import ABS_PATH, HEADERS_PATH, VTABLE_PATH, THUMB_MODE

g_parsed_symbols = []

def should_parse_sym(sym: str):
    return sym.find(':') != -1

def parse_sym(sym: str):
    dtorPrefix = ""
    tokens = sym.split(" = ")
    addr = int(tokens[1], base=16)
    tokens = tokens[0].split('::')
    sig = tokens[-1]
    name = tokens[0]

    if name.find('*/') != -1:
        name = name.replace("/* ", "")
        toks = name.split("*/ ")
        dtorPrefix = "/* " + toks[0] + "*/ "
        name = toks[1]

    for i in range(1, len(tokens) - 1):
        name += "__" + tokens[i]

    return [name, dtorPrefix + sig, addr]

def read_vtable(class_name: str):
    class_name_safe = class_name.replace("::", "__")
    try:
        vtable = []
        vth = open(VTABLE_PATH + class_name_safe + ".vt", "r")
        for item in vth.read().split('\n'):
            if item != '':
                vtable.append(int(item, base=16))
        vth.close()
        return vtable
    except:
        print(f'INFO: could not read vtable of {class_name}')
        return []

def remove_ns(class_name: str):
    tokens = class_name.split('::')
    if len(tokens) > 1:
        s = "/* "
        for i in range(len(tokens) - 1):
            s += tokens[i] + "::"
        s += " */ " + tokens[len(tokens) - 1]
        return s
    return class_name

# Open and parse symbols

sh = open(ABS_PATH + "symbols.txt", "r")
symlist = sh.read().split('\n')

for sym in symlist:
    if not should_parse_sym(sym):
        continue

    parsed = parse_sym(sym)
    g_parsed_symbols.append(parsed)

sh.close()

# Open and load typeinfos

tyh = open(ABS_PATH + "typeinfos.txt", "r")
tylist = tyh.read().split('\n')

for tyinfo in tylist:
    # Parse typeinfo
    class_name = tyinfo.split('|')[0]
    class_name_safe = class_name.replace("::", "__")
    bases = tyinfo.split('|')[1:]

    for i in range(len(bases)):
        bases[i] = remove_ns(bases[i])

    # Load vtable
    vtable = read_vtable(class_name)

    # Get methods
    methods = []

    for candidate in g_parsed_symbols:
        if candidate[0] == class_name_safe:
            methods.append([candidate[2], candidate[1]])

    methods.sort(reverse=True, key=lambda m: m[0])

    # Start header
    try:
        header = open(HEADERS_PATH + class_name_safe + ".h", "w")

        header.write(f"class {remove_ns(class_name)}")

        if len(bases) > 0:
            header.write(f"\n    : public {bases[0]}")
            for i in range(1, len(bases)):
                header.write(f",\n    public {bases[i]}")

        header.write("\n{\n")

        # Write methods

        for method in methods:
            # virtuals come later
            if vtable.count(method[0] & (0xFFFFFFFF - int(THUMB_MODE))) == 0:
                if (method[1].find('~') != -1):
                    header.write(f"    {method[1]};\n")
                else:
                    header.write(f"    /* TODO: change type! */ void {method[1]};\n")

        # Write virtuals, if any
        if len(vtable) > 0:
            header.write("\n    /* Virtual methods */\n\n")

            for vtentry in vtable:
                for method in methods:
                    if vtentry == (method[0] & (0xFFFFFFFF - int(THUMB_MODE))):
                        if method[1].find('~') != -1:
                            header.write(f"    {method[1]};\n")
                        else:
                            header.write(f"    virtual /* TODO: change type! */ void {method[1]};\n")

        # End header
        header.write("};")
        header.close()
    except:
        print(f'WARNING: could not dump class "{class_name}"')