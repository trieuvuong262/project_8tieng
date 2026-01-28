import os
import django
import requests
from django.core.files.base import ContentFile

# 1. Setup môi trường
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_8tieng.settings')
django.setup()

from core.models import Product

def create_fake_shop():
    print("🚀 Đang làm sạch và nạp dữ liệu Shop...")
    
    # Dữ liệu mẫu với link Affiliate thật (để test) và ảnh đẹp
    data = [
        {
            "name": "Bàn phím cơ Custom cực chill",
            "price": "1.250.000đ",
            "url": "https://shopee.vn/search?keyword=mechanical+keyboard",
            "img": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=600",
            "cat": "Phụ kiện"
        },
        {
            "name": "Đèn bàn làm việc kiến trúc sư",
            "price": "450.000đ",
            "url": "https://shopee.vn/search?keyword=pixar+lamp",
            "img": "https://images.unsplash.com/photo-1534073828943-f801091bb18c?w=600",
            "cat": "Đèn bàn"
        },
        {
            "name": "Chậu cây Monstera để bàn",
            "price": "180.000đ",
            "url": "https://shopee.vn/search?keyword=monstera+mini",
            "img": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=600",
            "cat": "Cây xanh"
        },
        {
            "name": "Loa Bluetooth Retro Marshall",
            "price": "3.500.000đ",
            "url": "https://shopee.vn/search?keyword=marshall+emberton",
            "img": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600",
            "cat": "Điện tử"
        }
    ]

    for item in data:
        # Kiểm tra xem sản phẩm đã tồn tại chưa để tránh trùng lặp
        product, created = Product.objects.update_or_create(
            name=item['name'],
            defaults={
                'price_display': item['price'],
                'affiliate_url': item['url'],
                'category': item['cat'],
                'is_active': True,
                'is_hot': True,
                'description': "Sản phẩm decor giúp tăng 200% cảm hứng làm việc."
            }
        )

        if created or not product.image:
            try:
                print(f"📸 Đang tải ảnh cho: {item['name']}...")
                response = requests.get(item['img'], timeout=10)
                if response.status_code == 200:
                    # Lưu ảnh vào thư mục media/shop_decor/
                    product.image.save(
                        f"{product.id}_decor.jpg", 
                        ContentFile(response.content), 
                        save=True
                    )
            except Exception as e:
                print(f"❌ Lỗi tải ảnh: {e}")

    print("✨ Xong! Truy cập /shop_page/ để xem kết quả.")

if __name__ == "__main__":
    create_fake_shop()