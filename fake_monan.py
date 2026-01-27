import os
import django
import random
import requests
from faker import Faker
from django.core.files.base import ContentFile

# ==============================================================================
# 1. CẤU HÌNH DJANGO
# ==============================================================================
# ⚠️ HÃY SỬA DÒNG DƯỚI ĐÂY THÀNH TÊN PROJECT CỦA BẠN
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_8tieng.settings') 
django.setup()

from core.models import Restaurant, Dish

# ==============================================================================
# 2. CHUẨN BỊ DỮ LIỆU
# ==============================================================================
fake = Faker('vi_VN')

# Dữ liệu Logic: Loại hình -> Danh sách món ăn
FOOD_DATA = {
    'Cơm tấm': ['Cơm tấm sườn bì chả', 'Cơm tấm sườn nướng', 'Cơm tấm chả trứng', 'Cơm tấm gà nướng', 'Canh khổ qua'],
    'Phở': ['Phở bò tái', 'Phở bò nạm', 'Phở gà ta', 'Phở đặc biệt', 'Quẩy giòn', 'Trứng chần'],
    'Bún đậu': ['Bún đậu thập cẩm', 'Bún đậu thịt luộc', 'Chả cốm chiên', 'Nem chua rán', 'Dồi sụn nướng'],
    'Mì Ý & Pizza': ['Pizza Hải sản', 'Pizza Bò bằm', 'Mì Ý sốt kem', 'Mì Ý bò bằm', 'Khoai tây chiên'],
    'Đồ uống': ['Trà sữa trân châu', 'Trà đào cam sả', 'Cà phê sữa đá', 'Bạc xỉu', 'Sinh tố bơ'],
    'Cơm văn phòng': ['Cơm thịt kho trứng', 'Cơm cá kho tộ', 'Cơm gà xối mỡ', 'Cơm bò xào', 'Canh chua cá'],
    'Lẩu & Nướng': ['Lẩu Thái', 'Lẩu bò', 'Ba chỉ bò Mỹ nướng', 'Nầm heo nướng', 'Bạch tuộc nướng'],
    'Bánh mì': ['Bánh mì thịt nướng', 'Bánh mì chảo', 'Bánh mì ốp la', 'Bánh mì xíu mại', 'Sữa đậu nành']
}

PREFIX_NAMES = ['Quán', 'Tiệm', 'Bếp', 'Nhà hàng', 'Góc', 'Tiệm ăn']
MIDDLE_NAMES = ['Cô', 'Chú', 'Bà', 'Anh', 'Mẹ', 'Sài Gòn', 'Hà Nội', 'Phố', 'Xóm']
END_NAMES = ['Ba', 'Tư', 'Bảy', 'Mập', 'Béo', 'Gia Truyền', 'Ngon', 'Xinh', 'Vintage']

# Kho ảnh random (Unsplash)
FOOD_IMAGES = [
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600",
    "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=600",
    "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600",
    "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=600",
    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=600",
    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600",
    "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600",
]

def generate_restaurant_name(category):
    return f"{category} {random.choice(MIDDLE_NAMES)} {random.choice(END_NAMES)}"

def create_fake_data(n=50):
    print(f"🚀 Bắt đầu tạo {n} quán ăn và thực đơn...")
    
    categories_list = list(FOOD_DATA.keys())
    
    count = 0
    for _ in range(n):
        try:
            category = random.choice(categories_list)
            
            res_name = generate_restaurant_name(category)
            if random.random() < 0.3: 
                res_name = f"{random.choice(PREFIX_NAMES)} {random.choice(END_NAMES)}"
            
            # --- SỬA LỖI Ở ĐÂY: Dùng fake.city() thay vì fake.city_name() ---
            try:
                # Thử tạo địa chỉ kiểu Việt Nam
                address = f"{random.randint(1, 999)} {fake.street_name()}, {fake.city()}"
            except:
                # Nếu lỗi thì dùng address() mặc định
                address = fake.address()

            rating = round(random.uniform(3.8, 5.0), 1)
            review_count = random.randint(10, 500)
            
            image_url = random.choice(FOOD_IMAGES)
            response = requests.get(image_url, timeout=5)
            
            if response.status_code == 200:
                restaurant = Restaurant(
                    name=res_name,
                    address=address,
                    rating=rating,
                    review_count=review_count,
                    category=category,
                    url_foody='https://www.foody.vn'
                )
                
                file_name = f"res_{random.randint(10000,99999)}.jpg"
                restaurant.image.save(file_name, ContentFile(response.content), save=True)
                
                # Tạo món ăn
                possible_dishes = FOOD_DATA[category]
                selected_dishes = random.sample(possible_dishes, k=random.randint(3, min(5, len(possible_dishes))))
                
                for dish_name in selected_dishes:
                    Dish.objects.create(name=dish_name, restaurant=restaurant)

                count += 1
                print(f"✅ [{count}/{n}] Xong: {res_name}")
            else:
                print(f"⚠️ Lỗi tải ảnh cho quán {res_name}")

        except Exception as e:
            print(f"❌ Lỗi: {e}")

    print("=" * 50)
    print(f"🎉 Hoàn tất! Đã thêm {count} quán ăn.")

if __name__ == '__main__':
    create_fake_data(50)