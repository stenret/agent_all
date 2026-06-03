"""订单管理路由 — 直接 API 调用"""

from fastapi import APIRouter

from models.schemas import PayRequest, OrderQueryRequest, RefundRequest, SeatCheckRequest, SeatLockRequest
from tools.seat_manager import check_seats, lock_seats
from tools.order_manager import create_order, query_order, refund
from tools.payment import pay_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/seats/check")
async def seats_check(req: SeatCheckRequest):
    """查看座位"""
    result = check_seats(req.show_id, req.section)
    return {"result": result}


@router.post("/seats/lock")
async def seats_lock(req: SeatLockRequest):
    """锁定座位"""
    result = lock_seats(req.show_id, req.seats, req.session_id)
    return {"result": result}


@router.post("/pay")
async def pay(req: PayRequest):
    """支付订单"""
    result = pay_order(req.order_id, req.payment_method)
    return {"result": result}


@router.post("/query")
async def query(req: OrderQueryRequest):
    """查询订单"""
    result = query_order(req.order_id, req.session_id)
    return {"result": result}


@router.post("/refund")
async def refund_order(req: RefundRequest):
    """退票"""
    result = refund(req.order_id, req.reason)
    return {"result": result}
