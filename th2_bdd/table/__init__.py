import dataclasses
from typing import TypeVar, Generic, Type

T = TypeVar("T")


class Table(Generic[T]):
    def __init__(self, row_type: Type[T]):
        self.row_type = row_type
        self.inited_row_type = None
        self._rows = []

    def parse(self, table):
        rows = [[r.rstrip(" ").lstrip(" ") for r in row[1:-1].split("|")] for row in table.split("\n")]
        header = rows.pop(0)
        if [f.name for f in dataclasses.fields(self.row_type)] != header:
            raise ValueError(f"Invalid table header {header}")
        self._rows = [self.row_type(*row) for row in rows]
        return self

    def __getitem__(self, item) -> T:
        return self._rows[item]

    @property
    def rows(self):
        return self._rows

    def __call__(self, tbl):
        return self.parse(tbl)


    def to_table(self):
        result = [dataclasses.asdict(row) for row in self.rows]
        return {"type": "table", "rows": result}


def table(row_type):
    def decorator(function):
        def wrapper(*args, **kwargs):
            tbl = kwargs.get("table", None)
            if tbl:
                tbl: row_type = Table(row_type=row_type).parse(tbl)
                kwargs["table"] = tbl
            result = function(*args, **kwargs)
            return result

        return wrapper

    return decorator