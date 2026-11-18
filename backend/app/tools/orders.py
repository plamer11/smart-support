
from langchain_core.tools import tool

ORDERS = {
    "A1001": {
        "status": "已发货",
        "carrier": "顺丰速运",
        "eta": "2026-09-24",
        "items": "北欧风桌面收纳盒 x1",
    },
    "A1002": {
        "status": "拣货中",
        "carrier": "尚未分配承运商",
        "eta": "预计 2026-09-25 发出",
        "items": "纯棉四件套 x1",
    },
    "A1003": {
        "status": "已签收",
        "carrier": "京东物流",
        "eta": "已于 2026-09-18 签收",
        "items": "落地穿衣镜 x1",
    },
}

REFUND_RULES = {
    "标准": "签收后 7 天内可无理由退货，需保持商品完好；审核通过后 3 个工作日内原路退款。",
    "大件": "家具等大件商品签收后 7 天内可退货，需支付往返运费；退款在收货验收后 5 个工作日内处理。",
    "定制": "定制类商品不支持无理由退货；存在质量问题时可免费返厂维修或重做。",
}


@tool
def query_order(order_id: str) -> str:

    order = ORDERS.get(order_id.strip().upper())
    if not order:
        return f"未找到订单 {order_id}，请确认订单号是否正确（示例：A1001）。"
    return (
        f"订单 {order_id}（{order['items']}）：状态「{order['status']}」，"
        f"承运商：{order['carrier']}，{order['eta']}。"
    )


@tool
def query_logistics(order_id: str) -> str:

    order = ORDERS.get(order_id.strip().upper())
    if not order:
        return f"未找到订单 {order_id} 的物流信息。"
    if order["status"] == "已签收":
        return f"订单 {order_id} 已于 2026-09-18 由本人签收，物流已完结。"
    return (
        f"订单 {order_id} 最新轨迹：包裹已到达【杭州转运中心】，"
        f"下一站【上海浦东分拨中心】，承运商 {order['carrier']}。"
    )


@tool
def refund_policy(order_type: str = "标准") -> str:

    rule = REFUND_RULES.get(order_type, REFUND_RULES["标准"])
    return f"【{order_type}商品退款政策】{rule}"
