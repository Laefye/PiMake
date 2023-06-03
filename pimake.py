import argparse
import json
import os
import subprocess

class Project:
    def __init__(self, directory = "", name = "") -> None:
        self.directory = os.path.abspath(directory)
        self.name = name

    def info(self) -> str:
        return ''

    def placeholder(self, val) -> str:
        return val.replace("$project$", self.directory)

class Sources(Project):
    def __init__(self, directory="", name="", sources=[], language="", libraries=[]) -> None:
        super().__init__(directory, name)
        self.sources = sources
        self.language = language
        self.libraries = libraries

    def abs_sources(self) -> list[str]:
        sources = []
        for source in self.sources:
            sources.append(os.path.abspath(self.directory + '/' + source))
        return sources
    
    def output_name(self) -> str:
        return self.name

class Library(Project):
    def includes(self) -> str:
        return []
    def library_path(self) -> str:
        return []
    def library(self) -> str:
        return []
    
class ExternalDynamicLibrary(Library):
    def __init__(self, directory="", name="", includes=[], libraries_path = [], libraries=[]) -> None:
        super().__init__(directory, name)
        self.inc = includes
        self.libraries_path = libraries_path
        self.libraries = libraries
    
    def library(self) -> str:
        return list(map(lambda x: f'-l{x}', self.libraries))

    def library_path(self) -> str:
        return list(map(lambda x: f'-L{x}', map(os.path.abspath, map(self.placeholder, self.libraries_path))))

    def includes(self) -> str:
        return list(map(lambda x: f'-I{x}', map(os.path.abspath, map(self.placeholder, self.inc))))
    
    def info(self) -> str:
        info = f'{self.name}: External Dynamic Library\n'
        info += ' Library:\n'
        for library in self.libraries:
            info += f'  {library}\n'
        info += ' Library path:\n'
        for library in self.libraries_path:
            info += f'  {library}\n'
        info += ' Include path:\n'
        for library in self.inc:
            info += f'  {library}\n'
        return info

class Executable(Sources):
    def __init__(self, directory = "", name = "", sources = [], lang = "", libraries=[]) -> None:
        super().__init__(directory, name, sources, lang, libraries)
    
    def info(self) -> str:
        info = f'{self.name}: Executable ({self.language})\n'
        info += ' Sources:\n'
        for source in self.sources:
            info += f'  {source}\n'
        return info
    
    def output_name(self) -> str:
        if os.name == 'nt':
            return self.name + '.exe'
        else:
            return self.name

class Preset:
    def __init__(self, name = "", language = "") -> None:
        self.name = name
        self.language = language
    
    def check(self) -> bool:
        return True
    
    def compiler(self) -> str:
        return ''
    
    def linker(self) -> str:
        return ''

class ClangPreset(Preset):
    def __init__(self) -> None:
        super().__init__("clang", "C")

    def check(self) -> bool:
        if os.name == "nt":
            self.cc = "C:/Program Files/LLVM/bin/clang.exe"
            self.ld = "C:/Program Files/LLVM/bin/clang.exe"
        elif os.name == "posix":
            self.cc = "/usr/bin/clang"
            self.ld = "/usr/bin/clang"
        if os.path.exists(self.cc) and os.path.exists(self.ld):
                return True
        return False
    
    def compiler(self) -> str:
        return self.cc

    def linker(self) -> str:
        return self.ld 
    
class ClangCPPPreset(ClangPreset):
    def __init__(self) -> None:
        super().__init__()
        self.language = 'C++'

    def check(self) -> bool:
        if os.name == "nt":
            self.cc = "C:/Program Files/LLVM/bin/clang++.exe"
            self.ld = "C:/Program Files/LLVM/bin/clang++.exe"
        elif os.name == "posix":
            self.cc = "/usr/bin/clang++"
            self.ld = "/usr/bin/clang++"
        if os.path.exists(self.cc) and os.path.exists(self.ld):
            return True
        return False
    
class GccPreset(Preset):
    def __init__(self) -> None:
        super().__init__()
        self.language = 'C'

    def check(self) -> bool:
        if os.name == "posix":
            self.cc = "/usr/bin/gcc"
            self.ld = "/usr/bin/gcc"
            if os.path.exists(self.cc) and os.path.exists(self.ld):
                return True
        return False
    
    def compiler(self) -> str:
        return self.cc

    def linker(self) -> str:
        return self.ld 
    
class GccCPPPreset(GccPreset):
    def __init__(self) -> None:
        super().__init__()
        self.language = 'C++'

    def check(self) -> bool:
        if os.name == "posix":
            self.cc = "/usr/bin/g++"
            self.ld = "/usr/bin/g++"
            if os.path.exists(self.cc) and os.path.exists(self.ld):
                return True
        return False
    
presets = [
    ClangPreset(),
    ClangCPPPreset(),
    GccPreset(),
    GccCPPPreset(),
    Preset(),
]

class BuildConfiguration:
    def __init__(self, compiler = "", linker = "", elements = []) -> None:
        self.elements = {}
        for element in elements:
            if isinstance(element, Sources):
                self.elements[element.name] = {}
                currentPreset = Preset()
                for preset in presets:
                    if preset.language == element.language and preset.check():
                        currentPreset = preset
                        break
                self.elements[element.name]['compiler'] = currentPreset.compiler()
                self.elements[element.name]['linker'] = currentPreset.linker()
                self.elements[element.name]['output'] = element.output_name()
                self.elements[element.name]['sources'] = element.abs_sources()
                self.elements[element.name]['linker-flags'] = []
                self.elements[element.name]['compiler-flags'] = []
                for library in element.libraries:
                    for lib in elements:
                        if isinstance(lib, Library) and lib.name == library:
                            self.elements[element.name]['linker-flags'].extend(lib.library_path())
                            self.elements[element.name]['linker-flags'].extend(lib.library())
                            self.elements[element.name]['compiler-flags'].extend(lib.includes())
                            break

    def save(self):
        with open('pimake-build.json', 'w', encoding='utf-8') as f:
            json.dump({
                'elements': self.elements,
            }, f, indent=4)

    def load(self):
        with open('pimake-build.json', 'r', encoding='utf-8') as f:
            file = json.load(f)
            self.elements = file['elements']

    def build(self):
        # Sources only
        for element in self.elements:
            for source in self.elements[element]['sources']:
                cmd = [
                    self.elements[element]['compiler'],
                    *self.elements[element]['compiler-flags'],
                    '-c',
                    source,
                    '-o',
                    source + '.o',
                ]
                subprocess.run(cmd)
        # Link
        for element in self.elements:
            cmd = [
                self.elements[element]['linker'],
                *self.elements[element]['linker-flags'],
                *map(lambda x: x + '.o', self.elements[element]['sources']),
                '-o',
                self.elements[element]['output'],
            ]
            subprocess.run(cmd)
            
def k_or_v(dic, k, df):
    if k not in dic:
        return df
    return dic[k]

def load_configuration(f):
    elements = []
    configuration = json.load(f)
    for elementname in configuration:
        if configuration[elementname]['type'] == "executable":
            elements.append(Executable(
                directory=os.path.dirname(f.name),
                name=elementname,
                sources=configuration[elementname]['sources'],
                lang=configuration[elementname]['lang'],
                libraries=(k_or_v(configuration[elementname], 'libraries', [])),
            ))
        elif configuration[elementname]['type'] == "external-dynamic-library":
            elements.append(ExternalDynamicLibrary(
                name=elementname,
                directory=os.path.dirname(f.name),
                libraries=configuration[elementname]['libraries'],
                libraries_path=k_or_v(configuration[elementname], 'libraries_path', []),
                includes=k_or_v(configuration[elementname], 'includes', []),
            ))
    return elements

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='pimake',
        description='Simple open-source software for build automation C/C++ projects'
    )
    parser.add_argument('-f', '--file', type=argparse.FileType(encoding='utf-8'), required=True)
    parser.add_argument('-I', '--info', action='store_true')
    parser.add_argument('-m', '--make', action='store_true')
    parser.add_argument('-b', '--build', action='store_true')
    args = parser.parse_args()
    
    elements = load_configuration(args.file)

    if args.info:
        for element in elements:
            print(element.info())
    
    if args.make:
        buildconfiguration = BuildConfiguration(
            elements=elements
        )
        buildconfiguration.save()
    if args.build:
        buildconfiguration = BuildConfiguration()
        buildconfiguration.load()
        buildconfiguration.build()
        