import strawberry
from typing import List, Optional
from schema.types import User, Product, Order
from utils.csv_parser import csv_parser

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        """Get all users"""
        user_dicts = csv_parser.get_users()
        return [User(**user_dict) for user_dict in user_dicts]

    @strawberry.field
    def user(self, id: int) -> Optional[User]:
        """Get user by ID"""
        user_dict = csv_parser.get_user_by_id(id)
        return User(**user_dict) if user_dict else None

    @strawberry.field
    def products(self) -> List[Product]:
        """Get all products"""
        product_dicts = csv_parser.get_products()
        return [Product(**product_dict) for product_dict in product_dicts]

    @strawberry.field
    def product(self, id: int) -> Optional[Product]:
        """Get product by ID"""
        product_dict = csv_parser.get_product_by_id(id)
        return Product(**product_dict) if product_dict else None

    @strawberry.field
    def orders(self) -> List[Order]:
        """Get all orders"""
        order_dicts = csv_parser.get_orders()
        return [Order(**order_dict) for order_dict in order_dicts]

    @strawberry.field
    def order(self, id: int) -> Optional[Order]:
        """Get order by ID"""
        order_dict = csv_parser.get_order_by_id(id)
        return Order(**order_dict) if order_dict else None

    @strawberry.field
    def orders_by_user(self, user_id: int) -> List[Order]:
        """Get orders by user ID"""
        order_dicts = csv_parser.get_orders_by_user_id(user_id)
        return [Order(**order_dict) for order_dict in order_dicts]

    @strawberry.field
    def orders_by_product(self, product_id: int) -> List[Order]:
        """Get orders by product ID"""
        order_dicts = csv_parser.get_orders_by_product_id(product_id)
        return [Order(**order_dict) for order_dict in order_dicts]