# Th2 pytest bdd plugin
This is the plugin for pytest, which uses pytest-bdd plugin and th2 as backend.

## Features
* Typed tables in feature file;
* Th2 client boilerplate isolation (auto th2 access factory creation, events hierarchy creation in background);
* Test context.

## Installation

- From PyPI  
  This package can be found on [PyPI](https://pypi.org/project/pytest-th2-bdd/ "pytest-th2-bdd").
    ```
    pip install pytest-th2-bdd
    ```

- From Source
    ```
    git clone https://github.com/th2-net/pytest-th2-bdd
    pip install pytest-th2-bdd/
    ```

## Available fixtures
### factory
This fixture yields th2 CommonFactory for which will be created from configuration located in `configs/` directory.

### ctx
This fixture is used for inter-steps communication. It has some important service items:

| key                  | purpose                                  |
|----------------------|------------------------------------------|
| `__ROOT__`           | root events for each feature             |
| `__SCENARIO__`       | current scenario root event              |
| `__SCENARIO_START__` | current scenario start datetime (in UTC) |
| `__STEP__`           | current step event                       |


## Requirements
* Prepared th2 test environment;
* Configuration for th2 CommonFactory in `configs/` directory;

## How to use tables
Imagine, that you need to pass data as table in some step:
```
| field1 | field2 | ... | fieldN |
| 1      | 2      | ... | 3      |
...
| valN   | valK   | ... | valM   |
```

1. You need to declare dataclass with header definition:
```python
@dataclass
class SomeRow:
    field1: str
    field2: str
    ...
    fieldN: str
```

2. Add field and converter at the desired step definition
```python
@given(
    parsers.cfparse(
        "some step description {var1} ... \n{table}",
    ),
    converters={"table": Table(SomeRow)}, # converter setup
)
def some_step(var1, table: Table[SomeRow]): # Syntax hints via generics
    ...
```

## How to start test process (with installed plugin)
```shell
pytest tests/
```

## How to start test process (without installed plugin)
```shell
export PYTHONPATH=path/to/directory/with/this/repository:$PYTHONPATH
pytest -p th2_bdd.pytest tests/
```
