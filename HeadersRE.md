# Headers contribution

If you want to contribute to the headers, follow this document.

## Unsupported version

If your target is currently not supported, you can dump the headers by yourself. This repo contains some tools:

1. [dump_funcs.py](tools/dump_funcs.py): use this tool to extract the function signatures from the **android** binary of the game (ie. `apk/lib/armeabi-v7a/libgame.so`, `apk/lib/armeabi-v7a/libcocos2dcpp.so`).
2. [dump_vtables.py](tools/dump_vtables.py): use this tool to dump the [vtables](https://en.wikipedia.org/wiki/Virtual_method_table) of the classes from the previously generated list. These are intermediate files necessary for building correct headers!
3. [dump_typeinfos.py](tools/dump_typeinfos.py): this tool dumps the bases every class inherits.

4. [gen_headers.py](tools/gen_headers.py): this tool uses the outputs of all the other tools in order to generate readable headers. Every access specifier defaults to `public`; moreover, every return type defaults to `void`. These should be manually changed.

The tools can be controlled by the [config.py](tools/config.py) file.

## Supported version

If your're done generating headers, or your target is already available on the [repo](https://github.com/gd-hyperdash/GeometryDash), you can start contributing in many ways:

- Every function using STL containers should be converted to use [our custom STL containers](https://github.com/gd-hyperdash/gdstl), including setting up a predefined link name using the `link_name` attribute.
- We would love for you to complete the classes by finding their related data members.
- In general, we'd like headers to look like as if RobTop wrote them; following the cocos2d-x design (camel case, usage of `CC_SYNTHESIZE`, data members ending with `_`, etc) is strongly encouraged.

When you're ready to submit a change, please file a PR [here](https://github.com/gd-hyperdash/GeometryDash/pulls). All requests are welcome!