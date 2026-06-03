"""座位管理工具 — 查看 / 锁定 / 释放座位"""

import json
import os
import random
import time
from threading import Lock

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# 内存中的锁座状态: {show_id: {seat_key: {"locked_at": timestamp, "session_id": str}}}
_seat_locks: dict[str, dict[str, dict]] = {}
_lock = Lock()


def _load_shows() -> list[dict]:
    path = os.path.join(_DATA_DIR, "shows.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["shows"]


def _load_venues() -> dict:
    path = os.path.join(_DATA_DIR, "venues.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["venues"]


def _get_show(show_id: str) -> dict | None:
    for s in _load_shows():
        if s["id"] == show_id:
            return s
    return None


def _get_venue(venue_id: str) -> dict | None:
    return _load_venues().get(venue_id)


def _make_seat_key(section: str, row: str, seat_num: int) -> str:
    return f"{section}-{row}-{seat_num:02d}"


def _clean_expired_locks(timeout_seconds: int = 300):
    """清理过期的锁（默认 5 分钟）"""
    now = time.time()
    with _lock:
        for show_id in list(_seat_locks.keys()):
            expired = [
                k for k, v in _seat_locks[show_id].items()
                if now - v["locked_at"] > timeout_seconds
            ]
            for k in expired:
                del _seat_locks[show_id][k]
            if not _seat_locks[show_id]:
                del _seat_locks[show_id]


def check_seats(show_id: str, section: str = "", limit: int = 20) -> str:
    """查看演出可用座位。

    Args:
        show_id: 演出ID
        section: 分区名称（为空则显示所有分区概览）
        limit: 最多显示的座位数
    """
    _clean_expired_locks()

    show = _get_show(show_id)
    if not show:
        return f"未找到演出ID '{show_id}'。"

    if show["available"] <= 0:
        return f"【{show['name']}】已售罄！"

    venue = _get_venue(show["venue_id"])
    if not venue:
        return "场馆信息异常。"

    # 获取该演出的已锁座位
    locked_in_show = _seat_locks.get(show_id, {})

    if section:
        # 查看指定分区的详细座位
        if section not in venue["sections"]:
            return f"分区 '{section}' 不存在。可选分区: {list(venue['sections'].keys())}"

        sec = venue["sections"][section]
        multiplier = sec["price_multiplier"]
        available_seats = []
        locked_seats = []

        for row_name in sec["rows"]:
            for seat_num in range(1, sec["seats_per_row"] + 1):
                key = _make_seat_key(section, row_name, seat_num)
                if key in locked_in_show:
                    locked_seats.append(key)
                else:
                    available_seats.append(key)

        # 模拟部分已售出
        random.seed(hash(show_id + section))
        sold_count = random.randint(1, max(1, len(available_seats) // 4))
        available_seats = available_seats[sold_count:]

        lines = [
            f"🎭 {show['name']}",
            f"📍 {section} 座位情况:",
            f"   💰 该区票价: {sec['price_multiplier']}x 基础价",
            f"   🟢 可用: {len(available_seats)}座",
            f"   🔒 已锁: {len(locked_seats)}座",
        ]

        if available_seats:
            lines.append(f"\n   推荐座位（前{min(limit, len(available_seats))}个）:")
            for seat in available_seats[:limit]:
                lines.append(f"   🎫 {seat}")

        return "\n".join(lines)

    else:
        # 显示所有分区概览
        lines = [f"🎭 {show['name']} — 座位分区概览:\n"]
        for sec_name, sec in venue["sections"].items():
            total = len(sec["rows"]) * sec["seats_per_row"]
            locked_count = sum(
                1 for k in locked_in_show if k.startswith(f"{sec_name}-")
            )
            random.seed(hash(show_id + sec_name))
            sold = random.randint(total // 6, total // 3)
            available = total - sold - locked_count
            price = int(show["base_price"] * sec["price_multiplier"])
            lines.append(
                f"  {sec_name}: {available}/{total}座可用 | "
                f"约¥{price}起 (x{sec['price_multiplier']})"
            )

        lines.append(f"\n如需查看具体分区座位，请指定分区名称。")
        return "\n".join(lines)


def lock_seats(show_id: str, seats: str, session_id: str = "default") -> str:
    """锁定座位（锁定后 5 分钟内需完成支付）。

    Args:
        show_id: 演出ID
        seats: 座位列表，格式如 "A区-A-03,A区-A-04" 或 "A区-A-03"
        session_id: 会话标识（用于关联订单）
    """
    _clean_expired_locks()

    show = _get_show(show_id)
    if not show:
        return f"❌ 未找到演出ID '{show_id}'。"

    if show["available"] <= 0:
        return f"❌ 【{show['name']}】已售罄。"

    venue = _get_venue(show["venue_id"])
    if not venue:
        return "❌ 场馆信息异常。"

    seat_list = [s.strip() for s in seats.split(",") if s.strip()]
    if not seat_list:
        return "❌ 请指定要锁定的座位。例如: A区-A-03"

    with _lock:
        if show_id not in _seat_locks:
            _seat_locks[show_id] = {}

        locked = []
        failed = []

        for seat_key in seat_list:
            if seat_key in _seat_locks[show_id]:
                failed.append(seat_key)
                continue

            # 验证座位是否存在
            parts = seat_key.split("-")
            if len(parts) != 3:
                failed.append(f"{seat_key}(格式错误)")
                continue

            section, row, seat_num_str = parts
            try:
                seat_num = int(seat_num_str)
            except ValueError:
                failed.append(f"{seat_key}(座位号错误)")
                continue

            venue_section = venue["sections"].get(section)
            if not venue_section:
                failed.append(f"{seat_key}(分区不存在)")
                continue

            if row not in venue_section["rows"]:
                failed.append(f"{seat_key}(排不存在)")
                continue

            if seat_num < 1 or seat_num > venue_section["seats_per_row"]:
                failed.append(f"{seat_key}(座位号超出范围)")
                continue

            # 锁定
            _seat_locks[show_id][seat_key] = {
                "locked_at": time.time(),
                "session_id": session_id,
            }
            locked.append(seat_key)

    lines = []
    if locked:
        # 计算总价
        total_price = 0
        for seat_key in locked:
            section = seat_key.split("-")[0]
            multiplier = venue["sections"].get(section, {}).get("price_multiplier", 1.0)
            total_price += int(show["base_price"] * multiplier)

        lines.append(f"✅ 锁座成功！已锁定 {len(locked)} 个座位:")
        for s in locked:
            lines.append(f"   🎫 {s}")
        lines.append(f"💰 合计: ¥{total_price}")
        lines.append(f"⏰ 请在 5 分钟内完成支付，否则座位将自动释放。")

    if failed:
        lines.append(f"\n❌ 以下座位锁定失败:")
        for s in failed:
            lines.append(f"   • {s}")

    return "\n".join(lines)


def release_seats(show_id: str, seats: str, session_id: str = "default") -> str:
    """释放已锁定的座位。

    Args:
        show_id: 演出ID
        seats: 座位列表，格式同 lock_seats
        session_id: 会话标识
    """
    seat_list = [s.strip() for s in seats.split(",") if s.strip()]

    with _lock:
        if show_id not in _seat_locks:
            return "该演出没有锁定的座位。"

        released = []
        for seat_key in seat_list:
            lock_info = _seat_locks[show_id].get(seat_key)
            if lock_info and lock_info["session_id"] == session_id:
                del _seat_locks[show_id][seat_key]
                released.append(seat_key)

    if released:
        return f"✅ 已释放 {len(released)} 个座位: {', '.join(released)}"
    return "没有可释放的座位。"
