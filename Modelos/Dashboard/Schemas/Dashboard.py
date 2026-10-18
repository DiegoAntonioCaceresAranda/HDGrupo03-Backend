from typing import List

from pydantic import BaseModel


class QuickStats(BaseModel):
    todaySales: float
    todayOrders: int
    newCustomersToday: int


class AttentionOrder(BaseModel):
    orderId: str
    customerName: str
    reason: str
    amount: str


class LowStockProduct(BaseModel):
    productId: str
    name: str
    stock: int
    threshold: int


class ActivityItem(BaseModel):
    id: str
    type: str
    message: str
    time: str


class HomeDashboardResponse(BaseModel):
    quickStats: QuickStats
    attentionOrders: List[AttentionOrder]
    lowStockProducts: List[LowStockProduct]
    activity: List[ActivityItem]
