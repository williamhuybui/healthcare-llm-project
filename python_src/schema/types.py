import strawberry
from typing import List, Optional
from utils.csv_parser import csv_parser

@strawberry.type
class User:
    id: int
    name: str
    email: str
    age: int
    city: str

    @strawberry.field
    def orders(self) -> List['Order']:
        """Get orders for this user"""
        order_dicts = csv_parser.get_orders_by_user_id(self.id)
        return [Order(**order_dict) for order_dict in order_dicts]

@strawberry.type
class Product:
    id: int
    name: str
    description: str
    price: float
    category: str
    stock: int

    @strawberry.field
    def orders(self) -> List['Order']:
        """Get orders for this product"""
        order_dicts = csv_parser.get_orders_by_product_id(self.id)
        return [Order(**order_dict) for order_dict in order_dicts]

@strawberry.type
class Order:
    id: int
    user_id: int
    product_id: int
    quantity: int
    order_date: str
    status: str

    @strawberry.field
    def user(self) -> Optional[User]:
        """Get the user for this order"""
        user_dict = csv_parser.get_user_by_id(self.user_id)
        return User(**user_dict) if user_dict else None

    @strawberry.field
    def product(self) -> Optional[Product]:
        """Get the product for this order"""
        product_dict = csv_parser.get_product_by_id(self.product_id)
        return Product(**product_dict) if product_dict else None