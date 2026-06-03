"""演出搜索工具 — 按条件检索演出信息"""

import json
import os
from typing import Any

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_shows() -> list[dict]:
    path = os.path.join(_DATA_DIR, "shows.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["shows"]


def _load_venues() -> dict:
    path = os.path.join(_DATA_DIR, "venues.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["venues"]


def search_shows(
    keyword: str = "",
    show_type: str = "",
    city: str = "",
    date_from: str = "",
    date_to: str = "",
    max_price: float = 0,
    limit: int = 5,
) -> str:
    """搜索演出。

    Args:
        keyword: 搜索关键词（演出名称/描述）
        show_type: 演出类型（演唱会/话剧/音乐剧/音乐会/脱口秀/展览/体育）
        city: 城市（北京/上海/广州/深圳/成都/杭州）
        date_from: 开始日期 YYYY-MM-DD
        date_to: 结束日期 YYYY-MM-DD
        max_price: 最高票价
        limit: 返回最多条数
    """
    shows = _load_shows()
    venues = _load_venues()
    results = []

    for s in shows:
        # 关键词匹配
        if keyword:
            kw = keyword.lower()
            if kw not in s["name"].lower() and kw not in s["description"].lower() and kw not in s["type"]:
                continue

        # 类型筛选
        if show_type and s["type"] != show_type:
            continue

        # 城市筛选
        if city and s["city"] != city:
            continue

        # 日期筛选
        if date_from and s["date"] < date_from:
            continue
        if date_to and s["date"] > date_to:
            continue

        # 价格筛选
        if max_price > 0 and s["base_price"] > max_price:
            continue

        results.append(s)

    if not results:
        return "未找到符合条件的演出。请尝试放宽搜索条件。"

    # 按日期排序
    results.sort(key=lambda x: x["date"])

    # 限制返回数量
    results = results[:limit]

    # 格式化输出
    lines = [f"找到 {len(results)} 场演出：\n"]
    for i, s in enumerate(results, 1):
        venue = venues.get(s["venue_id"], {})
        venue_name = venue.get("name", "未知场馆")
        prices = " / ".join(f"¥{p}" for p in s["price_tiers"])
        stock = "🟢 有票" if s["available"] > 50 else ("🟡 少量" if s["available"] > 0 else "🔴 售罄")
        lines.append(
            f"{i}. 【{s['type']}】{s['name']}\n"
            f"   🏟 {venue_name} | 📅 {s['date']} {s['time']}\n"
            f"   💰 {prices} | 🎫 {stock}(余{s['available']}张)\n"
            f"   📝 {s['description'][:80]}...\n"
            f"   🆔 演出ID: {s['id']}"
        )

    return "\n".join(lines)


def get_show_detail(show_id: str) -> str:
    """获取演出详情。

    Args:
        show_id: 演出ID
    """
    shows = _load_shows()
    venues = _load_venues()

    for s in shows:
        if s["id"] == show_id:
            venue = venues.get(s["venue_id"], {})
            venue_name = venue.get("name", "未知场馆")
            prices = " / ".join(f"¥{p}" for p in s["price_tiers"])
            stock = "有票" if s["available"] > 0 else "售罄"

            sections_info = []
            for sec_name, sec_data in venue.get("sections", {}).items():
                sections_info.append(f"     {sec_name}: {len(sec_data['rows'])}排 × {sec_data['seats_per_row']}座")

            return (
                f"🎭 {s['name']}\n"
                f"{'─' * 40}\n"
                f"📌 类型: {s['type']}\n"
                f"🏟 场馆: {venue_name}\n"
                f"📍 地址: {venue.get('address', '未知')}\n"
                f"📅 时间: {s['date']} {s['time']}\n"
                f"⏱ 时长: {s['duration_min']}分钟\n"
                f"💰 票价: {prices}\n"
                f"🎫 状态: {stock}（余{s['available']}张）\n"
                f"📝 简介: {s['description']}\n"
                f"🏟 座位分区:\n" + "\n".join(sections_info) +
                f"\n{'─' * 40}\n"
                f"🆔 演出ID: {s['id']}"
            )

    return f"未找到演出ID为 '{show_id}' 的演出。"


def search_shows_by_city(city: str, limit: int = 10) -> str:
    """按城市搜索演出。"""
    return search_shows(city=city, limit=limit)


def search_shows_by_type(show_type: str, limit: int = 10) -> str:
    """按类型搜索演出。"""
    return search_shows(show_type=show_type, limit=limit)
