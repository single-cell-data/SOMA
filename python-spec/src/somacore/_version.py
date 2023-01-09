"""Internal version information to indirect `_generated_version.py`.

setuptools imports this module to find the version for the package at *build
time*. We use this indirect module so that if the user has not run
``write-version-file`` (e.g. they just did a fresh checkout), ``pip install``
will still work. If we used ``setuptools.dynamic.version.attr`` and pointed it
at `somacore._generated_version` directly, installing from a fresh checkout
would fail.
"""

import pathlib
from typing import Any, Dict, Tuple, Union


def _read_version() -> Tuple[str, Tuple[Union[str, int], ...]]:
    version_contents: Dict[str, Any] = dict(
        version="0.0.0.dev+local-checkout",
        version_tuple=(0, 0, 0, "dev", "local-checkout"),
    )

    # We do this the hard way since neither
    #     from somacore import _generated_version
    # nor
    #     from . import _generated_version
    # will work in the build environment.
    gen_file = pathlib.Path(__file__).parent / "_generated_version.py"
    try:
        exec(gen_file.read_text(), version_contents)
    except Exception:
        # The generated file does not exist or is not valid.
        # Ignore it.
        pass
    return version_contents["version"], version_contents["version_tuple"]


version, version_tuple = _read_version()
