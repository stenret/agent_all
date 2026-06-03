"""模拟支付工具 — 处理订单支付"""

import json
import os
import time
import random

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


def pay_order(order_id: str, payment_method: str = "微信支付") -> str:
    """模拟支付订单。

    Args:
        order_id: 订单ID（由锁座操作生成）
        payment_method: 支付方式（微信支付/支付宝/银行卡）
    """
    orders_data = _load_orders()
    orders = orders_data.get("orders", {})

    if order_id not in orders:
        return f"❌ 订单 '{order_id}' 不存在。请先锁座生成订单。"

    order = orders[order_id]

    if order["status"] == "paid":
        return f"⚠️ 订单 '{order_id}' 已支付，无需重复支付。"

    if order["status"] == "refunded":
        return f"❌ 订单 '{order_id}' 已退票，无法支付。"

    if order["status"] == "cancelled":
        return f"❌ 订单 '{order_id}' 已取消，无法支付。"

    # 模拟支付（95% 成功率）
    time.sleep(0.3)  # 模拟网络延迟
    if random.random() < 0.95:
        order["status"] = "paid"
        order["paid_at"] = time.time()
        order["payment_method"] = payment_method
        orders_data["orders"] = orders
        _save_orders(orders_data)

        return (
            f"✅ 支付成功！\n"
            f"{'─' * 40}\n"
            f"📋 订单号: {order_id}\n"
            f"🎭 演出: {order.get('show_name', '未知')}\n"
            f"🎫 座位: {', '.join(order.get('seats', []))}\n"
            f"💰 金额: ¥{order.get('total_price', 0)}\n"
            f"💳 支付方式: {payment_method}\n"
            f"📅 支付时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'─' * 40}\n"
            f"🎉 购票成功！请按时入场观看。"
        )
    else:
        return (
            f"❌ 支付失败！\n"
            f"原因: 网络波动/余额不足（模拟）\n"
            f"请稍后重试或更换支付方式。订单 {order_id} 仍然有效。"
        )
