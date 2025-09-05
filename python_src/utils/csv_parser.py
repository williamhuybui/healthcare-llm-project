import pandas as pd
import os
from typing import List, Optional, Dict, Any

class CSVParser:
    def __init__(self):
        self.users = []
        self.products = []
        self.orders = []
    
    async def load_data(self):
        """Load data from CSV files"""
        try:
            base_path = os.path.join(os.path.dirname(__file__), '../../data')
            
            # Load CSV files
            users_df = pd.read_csv(os.path.join(base_path, 'users.csv'))
            products_df = pd.read_csv(os.path.join(base_path, 'products.csv'))
            orders_df = pd.read_csv(os.path.join(base_path, 'orders.csv'))
            
            # Convert to dictionaries
            self.users = users_df.to_dict('records')
            self.products = products_df.to_dict('records')
            self.orders = orders_df.to_dict('records')
            
            # Ensure proper data types
            self._process_data()
            
            print("CSV data loaded successfully")
            return {
                'users': self.users,
                'products': self.products,
                'orders': self.orders
            }
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            raise e
    
    def _process_data(self):
        """Process data to ensure correct types"""
        # Process users
        for user in self.users:
            user['id'] = int(user['id'])
            user['age'] = int(user['age'])
        
        # Process products
        for product in self.products:
            product['id'] = int(product['id'])
            product['price'] = float(product['price'])
            product['stock'] = int(product['stock'])
        
        # Process orders
        for order in self.orders:
            order['id'] = int(order['id'])
            order['user_id'] = int(order['user_id'])
            order['product_id'] = int(order['product_id'])
            order['quantity'] = int(order['quantity'])
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.users
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        return self.products
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        return self.orders
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return next((user for user in self.users if user['id'] == user_id), None)
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        return next((product for product in self.products if product['id'] == product_id), None)
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        return next((order for order in self.orders if order['id'] == order_id), None)
    
    def get_orders_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        """Get orders by user ID"""
        return [order for order in self.orders if order['user_id'] == user_id]
    
    def get_orders_by_product_id(self, product_id: int) -> List[Dict[str, Any]]:
        """Get orders by product ID"""
        return [order for order in self.orders if order['product_id'] == product_id]

# Global instance
csv_parser = CSVParser()