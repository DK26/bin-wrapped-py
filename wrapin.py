# MIT License
#
# Copyright 2022 David Krasnitsky <dikaveman@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import hashlib
import sys
import os
import base64
import zlib
import platform
from datetime import datetime

PY_CONTAINER_TEMPLATE = r'''# MIT License
#
# Copyright 2022 David Krasnitsky <dikaveman@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This `.py` file container was auto-generated by `{WRAPPER_NAME}`.
"""
import hashlib
import subprocess
import sys
import os
import base64
import zlib
import os.path
import platform
import stat


class Environment(object):
    """
    Metadata about the running environment.
    """
    PYTHON_VERSION = sys.version_info[0]
    PLATFORM = platform.system().lower()


class WrappedFile(object):
    """
    Auto-generated data about the wrapped file.
    """
    CHECKSUM = "{WRAPPED_FILE__CHECKSUM}"
    CHECKSUM_TYPE = "{WRAPPED_FILE__CHECKSUM_TYPE}"
    FILE_NAME = "{WRAPPED_FILE__FILE_NAME}"
    TARGET_PLATFORM = "{WRAPPED_FILE__TARGET_PLATFORM}"
    UTC_CREATION_DATETIME = "{WRAPPED_FILE__UTC_CREATION_DATETIME}"
    UTC_WRAP_DATETIME = "{WRAPPED_FILE__UTC_WRAP_DATETIME}"
    BASE64 = "{WRAPPED_FILE__BASE64}"


def unwrap_file(b64_data, file_name):

    if Environment.PYTHON_VERSION == 3:
        b64_data = bytes(b64_data, "utf-8")

    compressed = base64.b64decode(b64_data)
    data_bytes = zlib.decompress(compressed)
    with open(file_name, 'wb') as fp:
        fp.write(data_bytes)

    # Execute & Read permissions
    # To increase chance of success in unexpected environments
    os.chmod(file_name, stat.S_IXUSR | stat.S_IRUSR)


def checksum_file(file_path):

    with open(file_path, 'rb') as fp:
        file_data = fp.read()

    h = hashlib.sha1()
    h.update(file_data)

    return h.hexdigest()


def main():

    all_args = sys.argv[1:]

    if Environment.PLATFORM != WrappedFile.TARGET_PLATFORM:
        print("Failed: The executable targets the {} platform but you are running on the {} platform."
              .format(WrappedFile.TARGET_PLATFORM.title(), Environment.PLATFORM.title()))
        exit(-1)

    unwrap_directory = os.path.join(os.path.expanduser("~"), "unwrapped")
    unwrap_file_path = os.path.join(unwrap_directory, WrappedFile.FILE_NAME)

    if not os.path.isfile(unwrap_file_path) or not checksum_file(unwrap_file_path) == WrappedFile.CHECKSUM:
        
        try:
            os.makedirs(unwrap_directory)
        except OSError as e:
            pass

        unwrap_file(WrappedFile.BASE64, unwrap_file_path)

    run_args = [unwrap_file_path] + all_args

    if Environment.PLATFORM != "windows":
        run_args[0] = '.' + run_args[0]

    subprocess.call(run_args, shell=False)


if __name__ == '__main__':
    main()

'''


class Environment(object):
    PYTHON_VERSION = sys.version_info[0]
    PLATFORM = platform.system().lower()


def wrap_file(file_path):

    with open(file_path, 'rb') as fp:
        file_data = fp.read()

    h = hashlib.sha1()
    h.update(file_data)
    checksum = h.hexdigest()

    compressed = zlib.compress(file_data, 9)
    payload = base64.b64encode(compressed)

    return payload, checksum


def creation_time(file_path):
    if Environment.PLATFORM == "windows":
        ctime = os.path.getctime(file_path)
    else:
        ctime = os.stat(file_path).st_birthtime

    return datetime.fromtimestamp(ctime)


def equal_paths(path1, path2, *paths):
    paths = (path2,) + paths
    prev = os.path.abspath(os.path.normpath(os.path.normcase(path1)))
    for path in paths:
        if os.path.abspath(os.path.normpath(os.path.normcase(path))) == prev:
            prev = path
        else:
            return False
    return True


def main():

    parser = argparse.ArgumentParser(description="Wraps an executable binary file inside a Python source file, to be used as a script in a closed system.")

    parser.add_argument("executable", help="The executable binary file to be wrapped inside a Python source file.",
                        type=str)

    parser.add_argument("-o", "--output", help="Specify the output path for the Python source file.",
                        type=str, required=False)

    parser.add_argument("-t", "--target",
                        help="Specify the target operating system for the executable file: `Windows`, `Linux` or `Darwin`. "
                             "By default, the current operating system is selected. Mismatch of configurations with "
                             "the wrapped file will cause a failure of execution and will exit with an error.",
                        type=str, required=False)

    args = parser.parse_args()

    if args.target:
        target_platform = args.target
    else:
        target_platform = Environment.PLATFORM

    wrapper_name = os.path.basename(__file__)
    file_path = args.executable

    payload, checksum = wrap_file(file_path)

    if Environment.PYTHON_VERSION == 3:
        payload = str(payload, "utf-8")

    py_container_script = (
        PY_CONTAINER_TEMPLATE
        .replace("{WRAPPER_NAME}", wrapper_name)
        .replace("{WRAPPED_FILE__CHECKSUM}", checksum)
        .replace("{WRAPPED_FILE__CHECKSUM_TYPE}", "sha1")
        .replace("{WRAPPED_FILE__FILE_NAME}", os.path.basename(file_path))
        .replace("{WRAPPED_FILE__TARGET_PLATFORM}", target_platform)
        .replace("{WRAPPED_FILE__UTC_CREATION_DATETIME}", creation_time(file_path).isoformat())
        .replace("{WRAPPED_FILE__UTC_WRAP_DATETIME}", datetime.utcnow().isoformat())
        .replace("{WRAPPED_FILE__BASE64}", payload)
    )

    if Environment.PYTHON_VERSION == 3:
        py_container_script = bytes(py_container_script, "utf-8")

    if args.output:
        py_container_script_file = args.output
    else:
        py_container_script_file = file_path + '.wrapped.py'

    if equal_paths(wrapper_name, py_container_script_file):
        print("Failed: Attempted to overwrite the tool itself.")
        exit(-1)

    with open(py_container_script_file, 'wb') as fp:
        fp.write(py_container_script)


if __name__ == "__main__":
    main()
