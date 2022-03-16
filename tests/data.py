import dataclasses


@dataclasses.dataclass
class UserNameRow:
    UserName: str


@dataclasses.dataclass
class TagsRow:
    Price: str
    OrderQty: str
    Side: str
    OrderType: str
    OrderCapacity: str


@dataclasses.dataclass
class RejectRow:
    RefTagID: str
    RefMsgType: str
    BusinessRejectReason: str
    TargetCompID: str
    MsgType: str
    Text: str
    
    
trader = "DEMO-CONN1"

ds = "http://th2-qa:30000/th2-meta-env/backend"
conns = {
    "fix": "demo-conn1",
    "drop copy": "demo-dc1",
}
conn_by_trader = {}
statuses = {
    "UNKNOWN": "20",
    "on HALT": "2",
}
