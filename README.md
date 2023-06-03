## PiMake
Very simple open-source software for build automation for C/C++ (written in Python)

### How use
`pimake.json`:
```json
{
    "anyname": {
        "type": "external-dynamic-library",
        "libraries": ["m", "test"], // -lm -ltest
        "includes": ["$project$/libs/include"], // (optional) -I/project/path/libs/include
        "libraries_path": ["$project$/libs/lib"] // (optional) -L/project/libs/lib
    },
    "anotheranyname": {
        "type": "executable",
        "lang": "C++", // C or C++
        "sources": [
            "src/main.cpp" // C or C++ files
        ],
        "libraries": [ // (optional)
            "anyname" // use "anyname"
        ]
    }
}
```
Usage:
```bash
# Get info about project
python3 ../pimake.py -f pimake.json -I
# Make pimake-build.json (need every time when you change "pimake.json")
python3 ../pimake.py -f pimake.json -m
# Build all project
python3 ../pimake.py -f pimake.json -b
# Make pimake-build.json and build all project
python3 ../pimake.py -f pimake.json -m -b
```

### Note
- PiMake supports only "gcc-like" compilers (clang, mingw64, gcc, etc)
- PiMake automaticly can find only clang and gcc (only in unix-like)!