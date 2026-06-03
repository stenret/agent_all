"""演出查询路由 — 直接 API 调用（不走 Agent）"""

from fastapi import APIRouter

from models.schemas import ShowSearchRequest, ShowDetailRequest
from tools.show_search import search_shows, get_show_detail

router = APIRouter(prefix="/shows", tags=["shows"])


@router.post("/search")
async def search(req: ShowSearchRequest):
    """搜索演出"""
    result = search_shows(
        keyword=req.keyword,
        show_type=req.show_type,
        city=req.city,
        date_from=req.date_from,
        date_to=req.date_to,
        max_price=req.max_price,
        limit=req.limit,
    )
    return {"result": result}


@router.post("/detail")
async def detail(req: ShowDetailRequest):
    """查看演出详情"""
    result = get_show_detail(req.show_id)
    return {"result": result}


@router.get("/types")
async def show_types():
    """获取所有演出类型"""
    return {
        "types": ["演唱会", "话剧", "音乐剧", "音乐会", "脱口秀", "展览", "体育"]
    }


@router.get("/cities")
async def cities():
    """获取所有城市"""
    return {
        "cities": ["北京", "上海", "广州", "深圳", "成都", "杭州"]
    }
