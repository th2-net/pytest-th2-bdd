from setuptools import setup, find_packages

setup(
    name="th2-bdd",
    packages=list(map(lambda x: f"th2_bdd.{x}", find_packages(where="./th2_bdd"))),
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["th2_bdd = th2_bdd.pytest"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
    install_requires=[
        "pytest",
        "pytest-bdd",
        "th2-data-services",
        "th2-grpc-act-template",
        "th2-grpc-common",
        "th2-grpc-check1",
        "th2-common",
    ],
    version="0.0.1",
)
