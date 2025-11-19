"""
JSON fayllar bilan ishlash moduli - To'liq versiya
Barcha CRUD operatsiyalari bilan
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import config
import random
import logging

logger = logging.getLogger(__name__)


class JSONDatabase:
    """
    JSON fayllar bilan ishlash klassi
    Bu klass barcha ma'lumotlar bazasi operatsiyalarini amalga oshiradi
    """

    def __init__(self):
        """
        Initsializatsiya - data papkasini va fayllarni yaratish
        """
        # Data papkasini yaratish
        if not os.path.exists(config.DATA_DIR):
            os.makedirs(config.DATA_DIR)
            logger.info(f"✅ Data papka yaratildi: {config.DATA_DIR}")

        # Fayllarni initsializatsiya qilish
        self._init_file(config.PRODUCTS_FILE, [])
        self._init_file(config.ORDERS_FILE, [])
        self._init_file(config.USERS_FILE, [])
        self._init_file(config.CATEGORIES_FILE, [
            "👕 Kiyimlar",
            "👟 Poyabzal",
            "🎒 Sumkalar",
            "⌚ Aksessuarlar",
            "📱 Elektronika",
            "🏠 Uy-ro'zg'or"
        ])

        logger.info("✅ JSON Database initsializatsiya qilindi")

    def _init_file(self, filepath: str, default_data: Any):
        """
        Agar fayl bo'lmasa, default ma'lumotlar bilan yaratish

        Args:
            filepath: Fayl yo'li
            default_data: Default ma'lumotlar
        """
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Fayl yaratildi: {filepath}")

    def _read_json(self, filepath: str) -> Any:
        """
        JSON fayldan o'qish

        Args:
            filepath: Fayl yo'li

        Returns:
            Any: O'qilgan ma'lumotlar
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"❌ Faylni o'qishda xatolik ({filepath}): {e}")
            # Default qiymat qaytarish
            if filepath == config.CATEGORIES_FILE:
                return []
            return []

    def _write_json(self, filepath: str, data: Any):
        """
        JSON faylga yozish

        Args:
            filepath: Fayl yo'li
            data: Yoziladigan ma'lumotlar
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Faylga yozishda xatolik ({filepath}): {e}")

    # ==================== CATEGORIES ====================

    def get_categories(self) -> List[str]:
        """
        Barcha kategoriyalarni olish

        Returns:
            List[str]: Kategoriyalar ro'yxati
        """
        return self._read_json(config.CATEGORIES_FILE)

    def add_category(self, category: str) -> bool:
        """
        Yangi kategoriya qo'shish

        Args:
            category: Kategoriya nomi

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        categories = self.get_categories()

        # Dublikatni tekshirish
        if category in categories:
            logger.warning(f"⚠️ Kategoriya allaqachon mavjud: {category}")
            return False

        categories.append(category)
        self._write_json(config.CATEGORIES_FILE, categories)
        logger.info(f"✅ Kategoriya qo'shildi: {category}")
        return True

    def delete_category(self, category: str) -> bool:
        """
        Kategoriyani o'chirish (va unga tegishli barcha tovarlarni)

        Args:
            category: Kategoriya nomi

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        categories = self.get_categories()

        if category not in categories:
            logger.warning(f"⚠️ Kategoriya topilmadi: {category}")
            return False

        # Kategoriyani o'chirish
        categories.remove(category)
        self._write_json(config.CATEGORIES_FILE, categories)

        # Bu kategoriyaga tegishli tovarlarni ham o'chirish
        products = self.get_all_products()
        products = [p for p in products if p['category'] != category]
        self._write_json(config.PRODUCTS_FILE, products)

        logger.info(f"✅ Kategoriya o'chirildi: {category}")
        return True

    def update_category(self, old_name: str, new_name: str) -> bool:
        """
        Kategoriya nomini o'zgartirish

        Args:
            old_name: Eski nom
            new_name: Yangi nom

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        categories = self.get_categories()

        if old_name not in categories:
            logger.warning(f"⚠️ Kategoriya topilmadi: {old_name}")
            return False

        # Kategoriya nomini o'zgartirish
        idx = categories.index(old_name)
        categories[idx] = new_name
        self._write_json(config.CATEGORIES_FILE, categories)

        # Tovarlarni ham yangilash
        products = self.get_all_products()
        for product in products:
            if product['category'] == old_name:
                product['category'] = new_name
        self._write_json(config.PRODUCTS_FILE, products)

        logger.info(f"✅ Kategoriya o'zgartirildi: {old_name} -> {new_name}")
        return True

    # ==================== PRODUCTS ====================

    def add_product(self, category: str, name: str, description: str,
                    price: float, size: str = None, photo_id: str = None) -> Dict:
        """
        Yangi tovar qo'shish

        Args:
            category: Kategoriya
            name: Tovar nomi
            description: Tavsifi
            price: Narxi
            size: O'lchami/rangi (ixtiyoriy)
            photo_id: Telegram photo file_id (ixtiyoriy)

        Returns:
            Dict: Yaratilgan tovar
        """
        products = self._read_json(config.PRODUCTS_FILE)

        # Yangi ID yaratish
        new_id = max([p.get('id', 0) for p in products], default=0) + 1

        product = {
            'id': new_id,
            'category': category,
            'name': name,
            'description': description,
            'price': float(price),
            'size': size,
            'photo_id': photo_id,
            'is_available': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        products.append(product)
        self._write_json(config.PRODUCTS_FILE, products)

        logger.info(f"✅ Tovar qo'shildi: {name} (ID: {new_id})")
        return product

    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        Tovarni ID bo'yicha olish

        Args:
            product_id: Tovar ID

        Returns:
            Optional[Dict]: Tovar yoki None
        """
        products = self._read_json(config.PRODUCTS_FILE)
        for product in products:
            if product.get('id') == product_id:
                return product
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """
        Kategoriya bo'yicha mavjud tovarlarni olish

        Args:
            category: Kategoriya nomi

        Returns:
            List[Dict]: Tovarlar ro'yxati
        """
        products = self._read_json(config.PRODUCTS_FILE)
        return [
            p for p in products
            if p.get('category') == category and p.get('is_available', True)
        ]

    def get_all_products(self) -> List[Dict]:
        """
        Barcha tovarlarni olish (mavjud va mavjud bo'lmaganlarni)

        Returns:
            List[Dict]: Tovarlar ro'yxati
        """
        return self._read_json(config.PRODUCTS_FILE)

    def get_available_products(self) -> List[Dict]:
        """
        Faqat mavjud tovarlarni olish

        Returns:
            List[Dict]: Mavjud tovarlar ro'yxati
        """
        products = self._read_json(config.PRODUCTS_FILE)
        return [p for p in products if p.get('is_available', True)]

    def get_random_products(self, count: int = 3) -> List[Dict]:
        """
        Random tovarlarni olish (avtomatik post uchun)

        Args:
            count: Tovarlar soni

        Returns:
            List[Dict]: Random tovarlar
        """
        products = self.get_available_products()

        if len(products) == 0:
            logger.warning("⚠️ Mavjud tovarlar yo'q")
            return []

        if len(products) <= count:
            return products

        return random.sample(products, count)

    def update_product(self, product_id: int, **kwargs) -> bool:
        """
        Tovarni yangilash

        Args:
            product_id: Tovar ID
            **kwargs: Yangilanadigan maydonlar

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        products = self._read_json(config.PRODUCTS_FILE)

        for product in products:
            if product.get('id') == product_id:
                product.update(kwargs)
                self._write_json(config.PRODUCTS_FILE, products)
                logger.info(f"✅ Tovar yangilandi: ID {product_id}")
                return True

        logger.warning(f"⚠️ Tovar topilmadi: ID {product_id}")
        return False

    def delete_product(self, product_id: int) -> bool:
        """
        Tovarni o'chirish

        Args:
            product_id: Tovar ID

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        products = self._read_json(config.PRODUCTS_FILE)
        original_length = len(products)

        products = [p for p in products if p.get('id') != product_id]

        if len(products) < original_length:
            self._write_json(config.PRODUCTS_FILE, products)
            logger.info(f"✅ Tovar o'chirildi: ID {product_id}")
            return True

        logger.warning(f"⚠️ Tovar topilmadi: ID {product_id}")
        return False

    def toggle_product_availability(self, product_id: int) -> bool:
        """
        Tovar mavjudligini o'zgartirish

        Args:
            product_id: Tovar ID

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        products = self._read_json(config.PRODUCTS_FILE)

        for product in products:
            if product.get('id') == product_id:
                product['is_available'] = not product.get('is_available', True)
                self._write_json(config.PRODUCTS_FILE, products)
                status = "Mavjud" if product['is_available'] else "Mavjud emas"
                logger.info(f"✅ Tovar mavjudligi o'zgartirildi: ID {product_id} -> {status}")
                return True

        logger.warning(f"⚠️ Tovar topilmadi: ID {product_id}")
        return False

    # ==================== ORDERS ====================

    def create_order(self, user_id: int, username: str, product_id: int,
                     customer_name: str, phone: str, address: str,
                     quantity: int = 1) -> Dict:
        """
        Yangi buyurtma yaratish

        Args:
            user_id: Telegram user ID
            username: Telegram username
            product_id: Tovar ID
            customer_name: Mijoz ismi
            phone: Telefon
            address: Manzil
            quantity: Miqdor

        Returns:
            Dict: Yaratilgan buyurtma
        """
        orders = self._read_json(config.ORDERS_FILE)

        # Yangi ID yaratish
        new_id = max([o.get('id', 0) for o in orders], default=0) + 1

        # Buyurtma raqamini generatsiya qilish
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}"

        order = {
            'id': new_id,
            'order_number': order_number,
            'user_id': user_id,
            'username': username,
            'product_id': product_id,
            'customer_name': customer_name,
            'phone': phone,
            'address': address,
            'quantity': quantity,
            'status': 'yangi',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        orders.append(order)
        self._write_json(config.ORDERS_FILE, orders)

        logger.info(f"✅ Buyurtma yaratildi: {order_number}")
        return order

    def get_order(self, order_id: int) -> Optional[Dict]:
        """
        Buyurtmani ID bo'yicha olish

        Args:
            order_id: Buyurtma ID

        Returns:
            Optional[Dict]: Buyurtma yoki None
        """
        orders = self._read_json(config.ORDERS_FILE)
        for order in orders:
            if order.get('id') == order_id:
                return order
        return None

    def get_user_orders(self, user_id: int) -> List[Dict]:
        """
        Foydalanuvchi buyurtmalarini olish

        Args:
            user_id: Telegram user ID

        Returns:
            List[Dict]: Buyurtmalar ro'yxati
        """
        orders = self._read_json(config.ORDERS_FILE)
        user_orders = [o for o in orders if o.get('user_id') == user_id]

        # Sana bo'yicha saralash (eng yangi birinchi)
        return sorted(
            user_orders,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )

    def get_all_orders(self) -> List[Dict]:
        """
        Barcha buyurtmalarni olish

        Returns:
            List[Dict]: Buyurtmalar ro'yxati
        """
        orders = self._read_json(config.ORDERS_FILE)

        # Sana bo'yicha saralash
        return sorted(
            orders,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )

    def update_order_status(self, order_id: int, status: str) -> bool:
        """
        Buyurtma statusini yangilash

        Args:
            order_id: Buyurtma ID
            status: Yangi status

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """
        orders = self._read_json(config.ORDERS_FILE)

        for order in orders:
            if order.get('id') == order_id:
                order['status'] = status
                self._write_json(config.ORDERS_FILE, orders)
                logger.info(f"✅ Buyurtma statusi o'zgartirildi: {order.get('order_number')} -> {status}")
                return True

        logger.warning(f"⚠️ Buyurtma topilmadi: ID {order_id}")
        return False

    # ==================== USERS ====================

    def add_user(self, user_id: int, username: str = None,
                 first_name: str = None, last_name: str = None) -> Dict:
        """
        Foydalanuvchi qo'shish yoki yangilash

        Args:
            user_id: Telegram user ID
            username: Username (ixtiyoriy)
            first_name: Ism (ixtiyoriy)
            last_name: Familiya (ixtiyoriy)

        Returns:
            Dict: Foydalanuvchi ma'lumotlari
        """
        users = self._read_json(config.USERS_FILE)

        # Foydalanuvchi mavjudligini tekshirish
        for user in users:
            if user.get('user_id') == user_id:
                # Yangilash
                user['username'] = username
                user['first_name'] = first_name
                user['last_name'] = last_name
                self._write_json(config.USERS_FILE, users)
                return user

        # Yangi foydalanuvchi qo'shish
        user = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'is_blocked': False,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        users.append(user)
        self._write_json(config.USERS_FILE, users)

        logger.info(f"✅ Yangi foydalanuvchi: {user_id} (@{username})")
        return user

    def get_all_users(self) -> List[Dict]:
        """
        Barcha foydalanuvchilarni olish

        Returns:
            List[Dict]: Foydalanuvchilar ro'yxati
        """
        return self._read_json(config.USERS_FILE)

    def get_users_count(self) -> int:
        """
        Foydalanuvchilar sonini olish

        Returns:
            int: Foydalanuvchilar soni
        """
        users = self._read_json(config.USERS_FILE)
        return len(users)


# Global database obyekti
db = JSONDatabase()