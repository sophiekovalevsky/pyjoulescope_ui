# Copyright 2018 Jetperch LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Joulescope python setuptools module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
import setuptools
from setuptools.command.sdist import sdist
from distutils.command.clean import clean as dist_clean
import distutils.cmd
import os
import sys
import subprocess
import site
import shutil


VERSION = '0.4.6'  # CHANGE THIS VERSION!
JOULESCOPE_VERSION_MIN = '0.4.6'  # also update requirements.txt
MYPATH = os.path.abspath(os.path.dirname(__file__))
VERSION_PATH = os.path.join(MYPATH, 'joulescope_ui', 'version.py')


def find_qt_rcc():
    # Hack.  https://bugreports.qt.io/browse/PYSIDE-779
    # Fixed in 5.12.0 which is not released as of 2018 Oct 15.
    fname = shutil.which('pyside2-rcc')
    if fname:
        return fname
    for path in site.getsitepackages():
        fname = os.path.join(path, 'PySide2', 'pyside2-rcc.exe')
        if os.path.isfile(fname):
            return fname
    raise ValueError('qt rcc not found')


def convert_qt_ui():
    from pyside2uic import compileUi
    rcc_path = find_qt_rcc()
    path = os.path.join(MYPATH, 'joulescope_ui')
    ignore_filename = os.path.join(path, '.gitignore')
    with open(ignore_filename, 'wt') as ignore:
        ignore.write('# Automatically generated.  DO NOT EDIT\n')
        for source in os.listdir(path):
            source_base, ext = os.path.splitext(source)
            if ext == '.ui':
                target = source_base + '.py'
                with open(os.path.join(path, source), 'rt', encoding='utf8') as fsource:
                    with open(os.path.join(path, target), 'wt', encoding='utf8') as ftarget:
                        compileUi(fsource, ftarget, execute=False, indent=4, from_imports=True)
            elif ext == '.qrc':
                target = source_base + '_rc.py'
                rc = subprocess.run([rcc_path, os.path.join(path, source), '-o', os.path.join(path, target)])
                if rc.returncode:
                    raise RuntimeError('failed on .qrc file')
            else:
                continue
            ignore.write('%s\n' % target)


def update_version_py():
    with open(VERSION_PATH, 'wt') as fv:
        fv.write('# AUTOMATICALLY GENERATED BY setup.py\n')
        fv.write(f'VERSION = "{VERSION}"\n')


def clean_version_py():
    if os.path.isfile(VERSION_PATH):
        os.remove(VERSION_PATH)


def update_inno_iss():
    path = os.path.join(MYPATH, 'joulescope.iss')
    with open(path, 'rt') as fv:
        lines = fv.readlines()
    version_underscore = VERSION.replace('.', '_')
    for idx, line in enumerate(lines):
        if line.startswith('#define MyAppVersionUnderscores'):
            lines[idx] = f'#define MyAppVersionUnderscores "{version_underscore}"\n'
        elif line.startswith('#define MyAppVersion'):
            lines[idx] = f'#define MyAppVersion "{VERSION}"\n'
    with open(path, 'wt') as fv:
        fv.write(''.join(lines))


class CustomBuildQt(distutils.cmd.Command):
    """Custom command to build Qt resource file and Qt user interface modules."""

    description = 'Build Qt resource file and Qt user interface modules.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        convert_qt_ui()


class CustomSdistCommand(sdist):
    def run(self):
        update_version_py()
        update_inno_iss()
        convert_qt_ui()
        sdist.run(self)


class CustomCleanCommand(dist_clean):
    def run(self):
        clean_version_py()


if sys.platform.startswith('win'):
    PLATFORM_INSTALL_REQUIRES = ['pypiwin32>=223']
else:
    PLATFORM_INSTALL_REQUIRES = []


# Get the long description from the README file
with open(os.path.join(MYPATH, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='joulescope_ui',
    version=VERSION,
    description='Joulescope™ graphical user interface',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://www.joulescope.com',
    author='Jetperch LLC',
    author_email='joulescope-dev@jetperch.com',
    license='Apache',

    cmdclass={
        'qt': CustomBuildQt,
        'sdist': CustomSdistCommand,
        'clean': CustomCleanCommand,
    },

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: End Users/Desktop',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',

        # Pick your license as you wish
        'License :: OSI Approved :: Apache Software License',

        # Supported Python versions
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='joulescope ui gui "user interface"',

    packages=setuptools.find_packages(exclude=['docs', 'test', 'dist', 'build']),

    include_package_data=True,
    
    # See https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'json5>=0.6.1',
        'numpy>=1.15.2',
        'python-dateutil>=2.7.3',
        'pyside2>=5.13.0',
        # 'pyqtgraph>=0.11.0', eventually, but PEP 508 URL for now:
        'pyqtgraph @ https://github.com/jetperch/pyqtgraph/tarball/c8548b3246d29ee84a1ef76ebf63a5bb0e39c917#egg=pyqtgraph-0.11.0.dev0',
        'requests>=2.0.0',
        'joulescope>=' + JOULESCOPE_VERSION_MIN,
    ] + PLATFORM_INSTALL_REQUIRES,
    
    extras_require={
        'dev': ['check-manifest', 'Cython', 'coverage', 'wheel', 'pyinstaller'],
    },

    entry_points={
        'gui_scripts': [
            'joulescope_ui=joulescope_ui.main:run',
        ],
    },
    
    project_urls={
        'Bug Reports': 'https://github.com/jetperch/pyjoulescope_ui/issues',
        'Funding': 'https://www.joulescope.com',
        'Twitter': 'https://twitter.com/joulescope',
        'Source': 'https://github.com/jetperch/pyjoulescope_ui/',
    },
)
