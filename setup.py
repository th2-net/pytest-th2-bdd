import json
import os
import codecs
from setuptools import find_packages, setup


with open("package_info.json", "r") as file:
    package_info = json.load(file)

package_name = package_info["package_name"].replace("-", "_")
package_version = package_info["package_version"]


def read(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    return codecs.open(file_path, encoding="utf-8").read()


def get_reqs():
    with open("requirements.txt", "r") as file:
        requirements = [l.strip() for l in file.readlines() if not l.startswith("#") and l != "\n"]
    return requirements


setup(
    name=package_name,
    packages=find_packages(where="."),
    entry_points={"pytest11": ["pytest-th2-bdd = th2_bdd.pytest"]},
    classifiers=["Framework :: Pytest"],
    author='TH2-devs',
    author_email='th2-devs@exactprosystems.com',
    install_requires=get_reqs(),
    version=package_version,
)
