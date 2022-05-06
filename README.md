# Th2 BDD test example

## Requirements
* Prepared th2 test environment with this schema
* Set environment variable TH2_DS_ENTRYPOINT with url to rpt-data-provider
* Configuration for th2 CommonFactory in `configs` directory.

## How to start test process (without installed plugin)
```shell
pytest -p th2_bdd.pytest tests/
```

## How to start test process (with installed plugin)
```shell
pytest tests/
```
