"""订单管理工具 — 创建 / 查询 / 退票"""

import json
import os
import time
import uuid

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_ORDERS_FILE = os.path.join(_DATA_DIR, "orders.json")


def _load_orders() -> dict:
    if not os.path.exists(_ORDERS_FILE):
        return {"orders": {}}
    with open(_ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_orders(data: dict) -> None:
    with open(_ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_shows() -> list[dict]:
    path = os.path.join(_DATA_DIR, "shows.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["shows"]


def _get_show(show_id: str) -> dict | None:
    for s in _load_shows():
        if s["id"] == show_id:
            return s
    return None


def create_order(
    show_id: str,
    seats: str,
    total_price: float,
    session_id: str = "default",
) -> str:
    """创建订单（锁座后自动调用）。

    Args:
        show_id: 演出ID
        seats: 座位列表字符串
        total_price: 总价
        session_id: 会话标识
    """
    show = _get_show(show_id)
    if not show:
        return f"❌ 演出 '{show_id}' 不存在。"

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    seat_list = [s.strip() for s in seats.split(",") if s.strip()]

    orders_data = _load_orders()
    orders_data["orders"][order_id] = {
        "order_id": order_id,
        "show_id": show_id,
        "show_name": show["name"],
        "seats": seat_list,
        "total_price": total_price,
        "status": "locked",
        "session_id": session_id,
        "created_at": time.time(),
    }
    _save_orders(orders_data)

    return (
        f"📋 订单已创建\n"
        f"订单号: {order_id}\n"
        f"演出: {show['name']}\n"
        f"座位: {', '.join(seat_list)}\n"
        f"金额: ¥{total_price}\n"
        f"状态: 待支付（5分钟内完成支付）"
    )


def query_order(order_id: str = "", session_id: str = "") -> str:
    """查询订单。

    Args:
        order_id: 订单ID（精确查询）
        session_id: 会话ID（查询该会话的所有订单）
    """
    orders_data = _load_orders()
    orders = orders_data.get("orders", {})

    if order_id:
        if order_id in orders:
            order = orders[order_id]
            status_emoji = {
                "locked": "🔒 待支付",
                "paid": "✅ 已支付",
                "refunded": "↩️ 已退票",
                "cancelled": "❌ 已取消",
            }
            status = status_emoji.get(order["status"], order["status"])
            return (
                f"📋 订单详情\n"
                f"{'─' * 40}\n"
                f"订单号: {order['order_id']}\n"
                f"演出: {order.get('show_name', '未知')}\n"
                f"座位: {', '.join(order.get('seats', []))}\n"
                f"金额: ¥{order.get('total_price', 0)}\n"
                f"状态: {status}\n"
                f"创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order['created_at']))}"
            )
        return f"❌ 订单 '{order_id}' 不存在。"

    elif session_id:
        matched = {k: v for k, v in orders.items() if v.get("session_id") == session_id}
        if not matched:
            return f"会话 '{session_id}' 暂无订单。"

        lines = [f"📋 会话 '{session_id}' 的订单 ({len(matched)} 笔):\n"]
        for oid, order in matched.items():
            status = {"locked": "🔒", "paid": "✅", "refunded": "↩️", "cancelled": "❌"}.get(order["status"], "❓")
            lines.append(
                f"  {status} {oid} | {order.get('show_name', '未知')[:20]} | "
                f"¥{order.get('total_price', 0)} | "
                f"{time.strftime('%m/%d %H:%M', time.localtime(order['created_at']))}"
            )
        return "\n".join(lines)

    return "请提供订单ID或会话ID进行查询。"


def refund(order_id: str, reason: str = "") -> str:
    """退票。

    Args:
        order_id: 订单ID
        reason: 退票原因
    """
    orders_data = _load_orders()
    orders = orders_data.get("orders", {})

    if order_id not in orders:
        return f"❌ 订单 '{order_id}' 不存在。"

    order = orders[order_id]

    if order["status"] == "refunded":
        return f"⚠️ 订单 '{order_id}' 已退票，无需重复操作。"

    if order["status"] != "paid":
        return f"❌ 订单 '{order_id}' 当前状态为 '{order['status']}'，仅已支付订单可退票。"

    # 模拟退票（90% 成功率）
    time.sleep(0.3)
    if reason and "不同意" in reason:
        return "❌ 退票申请被拒绝（模拟）。退票原因不符合规定。"

    order["status"] = "refunded"
    order["refunded_at"] = time.time()
    order["refund_reason"] = reason or "用户申请退票"
    orders_data["orders"] = orders
    _save_orders(orders_data)

    return (
        f"✅ 退票成功！\n"
        f"订单号: {order_id}\n"
        f"退款金额: ¥{order.get('total_price', 0)}\n"
        f"预计 3-5 个工作日内退回到原支付账户。"
    )
