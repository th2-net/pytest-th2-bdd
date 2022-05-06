import os
import codecs
from setuptools import find_packages, setup


def read(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    return codecs.open(file_path, encoding="utf-8").read()


def get_version():
    version = read("VERSION")
    return version


setup(
    name="pytest-th2-bdd",
    packages=list(map(lambda x: f"th2_bdd.{x}", find_packages(where="./th2_bdd"))),
    entry_points={"pytest11": ["pytest_th2_bdd = th2_bdd.pytest"]},
    classifiers=["Framework :: Pytest"],
    author='TH2-devs',
    author_email='th2-devs@exactprosystems.com',
    install_requires=[
        "pytest",
        "pytest-bdd",
        "th2-data-services",
        "th2-grpc-act-template",
        "th2-grpc-common",
        "th2-grpc-check1",
        "th2-common",
    ],
    version=get_version(),
)
