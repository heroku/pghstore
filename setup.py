from __future__ import print_function
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
import os
import os.path
import sys

from setuptools import Extension, setup

# Allow us to import the version string
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from pghstore.version import VERSION  # noqa: E402


try:
    readme_f = open("README.rst")
    long_description = readme_f.read()
    readme_f.close()
except IOError:
    long_description = None

tests_require = None


# Most of the following codes to allow C extension building to fail were
# copied from MarkupSafe's setup.py script.
# https://github.com/mitsuhiko/markupsafe/blob/master/setup.py

ext_modules = [
    Extension(
        "pghstore._speedups", ["src/pghstore/_speedups.c"], extra_compile_args=["-O3"]
    )
]


ext_errors = CCompilerError, DistutilsExecError, DistutilsPlatformError
if sys.platform == "win32" and sys.version_info > (2, 6):
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors += (IOError,)


class BuildFailed(Exception):

    pass


class ve_build_ext(build_ext):
    """This class allows C extension building to fail."""

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]):  # works with Python 2 and 3
                raise BuildFailed()
            raise


def run_setup(with_speedups):
    setup(
        name="pghstore",
        packages=["pghstore"],
        package_dir={"": "src"},
        ext_modules=ext_modules,
        version=VERSION,
        description="PostgreSQL hstore formatter",
        long_description=long_description,
        license="MIT License",
        author="Hong Minhee",
        author_email="minhee" "@" "dahlia.kr",
        maintainer="Salesforce.com, Inc",
        url="https://github.com/heroku/pghstore",
        test_suite="pghstoretests.tests",
        install_requires=["six"],
        tests_require=tests_require,
        platforms=["any"],
        cmdclass={"build_ext": ve_build_ext},
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 2 :: Only",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Programming Language :: Python :: Implementation :: Stackless",
            "Topic :: Database",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )


def try_building_extension():
    try:
        run_setup(True)
    except BuildFailed:
        print("=" * 74)
        print("WARNING: The C extension could not be compiled,", end=" ")
        print("speedups are not enabled.")
        print("Failure information, if any, is above.")
        print("Retrying the build without the C extension now.")
        print()
        run_setup(False)
        print("=" * 74)
        print("WARNING: The C extension could not be compiled,", end=" ")
        print("speedups are not enabled.")
        print("Plain-Python installation succeeded.")
        print("=" * 74)


try_building_extension()
