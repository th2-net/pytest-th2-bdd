Feature: TS01_SessionManagement
    Scenario: TC01 Order is rejected on trading halt session
        Given following users are logged in to fix gateway
            |UserName       |
            |DEMO-CONN1     |
        And following users are logged in to drop copy gateway
            |UserName      |
            |DEMO-DC1      |
        And INSTR5 is on HALT (SecurityTradingStatus = 2)
        When user DEMO-CONN1 sends a new order with the following details
            | Price      | OrderQty     | Side | OrderType | OrderCapacity |
            | 50         | 10           | 1    | 2         | A             |
        Then DEMO-CONN1 receives BusinessMessageReject with given details
            | RefTagID      | RefMsgType     | BusinessRejectReason | TargetCompID | MsgType | Text               |
            | 48            | D              | 2                    | DEMO-CONN1   | j       | Trading halt       |
        And DEMO-DC1 user will not receive any messages
