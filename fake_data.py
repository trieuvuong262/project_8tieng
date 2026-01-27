import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker

# 1. Cấu hình môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_8tieng.settings')
django.setup()

# Import Models
from django.contrib.auth.models import User
from core.models import (
    UserProfile, ZoneConfig, Confession, 
    DocumentResource, FoodReview, Product, RewardItem
)

fake = Faker(['vi_VN']) # Sử dụng tiếng Việt

def create_zones():
    print("🔄 Đang thiết lập 4 Khu vực chức năng (Zone Config)...")
    ZoneConfig.objects.all().delete() # Xóa cũ

    zones = [
        {
            "zone_code": "ZONE_1",
            "display_name": "Bàn Làm Việc",
            "icon_name": "briefcase",
            "color_class": "bg-blue-50 text-blue-600",
            # Sáng: Ưu tiên 1 | Trưa: 3 | Chiều: 4
            "priority_morning": 1, "priority_work": 1, "priority_lunch": 3, "priority_chill": 4
        },
        {
            "zone_code": "ZONE_2",
            "display_name": "Pantry & Canteen",
            "icon_name": "coffee",
            "color_class": "bg-green-50 text-green-600",
            # Sáng: 2 | Trưa: 1 (HOT) | Chiều: 3
            "priority_morning": 2, "priority_work": 4, "priority_lunch": 1, "priority_chill": 3
        },
        {
            "zone_code": "ZONE_3",
            "display_name": "Góc Trà Đá",
            "icon_name": "message-circle",
            "color_class": "bg-orange-50 text-orange-600",
            # Sáng: 4 | Trưa: 2 (HOT) | Chiều: 1 (HOT)
            "priority_morning": 4, "priority_work": 3, "priority_lunch": 2, "priority_chill": 1
        },
        {
            "zone_code": "ZONE_4",
            "display_name": "Shop Decor",
            "icon_name": "shopping-bag",
            "color_class": "bg-purple-50 text-purple-600",
            # Lúc nào rảnh mới xem
            "priority_morning": 3, "priority_work": 2, "priority_lunch": 4, "priority_chill": 2
        },
    ]

    for z in zones:
        ZoneConfig.objects.create(**z)
    print("✅ Đã tạo xong 4 Zones.")

def create_users():
    print("🔄 Đang tạo User giả lập...")
    # Tạo Superuser nếu chưa có
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@8tieng.vn', 'admin123')
        print("   -> Đã tạo Superuser: admin / admin123")

    # Tạo User thường
    jobs = ['Designer', 'Accountant', 'Developer', 'HR Specialist', 'Marketing Exec', 'Intern']
    companies = ['FPT Software', 'VinGroup', 'Shopee', 'Ngân hàng ACB', 'Freelancer']
    
    users = []
    for _ in range(10):
        username = fake.user_name()
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_user(username=username, email=fake.email(), password='password123')
            u.first_name = fake.first_name()
            u.last_name = fake.last_name()
            u.save()
            
            # Tạo Profile
            UserProfile.objects.create(
                user=u,
                job_title=random.choice(jobs),
                company_name=random.choice(companies),
                total_kpi_points=random.randint(50, 5000),
                level_rank=random.choice(['Intern', 'Junior', 'Senior', 'Manager'])
            )
            users.append(u)
    
    print(f"✅ Đã tạo thêm {len(users)} users mẫu.")
    return users

def create_confessions(users):
    print("🔄 Đang tạo Drama công sở (Confessions)...")
    Confession.objects.all().delete()

    contents = [
        "Sếp bắt OT không lương thì có nên nghỉ không mọi người? Em mới làm được 2 tháng.",
        "Góc bóc phốt: Công ty X ở Cầu Giấy nợ lương 3 tháng chưa trả, anh em né gấp!",
        "Crush anh IT phòng bên mà không dám nói, ổng cứ lạnh lùng kiểu gì ấy hic.",
        "Lương 35 tuổi bao nhiêu là đủ sống ở Hà Nội nhỉ? Mình 15tr thấy chật vật quá.",
        "Review phỏng vấn ở Techcombank: Quy trình 3 vòng, hơi khó nhưng HR dễ thương.",
        "Trưa nay ăn gì ở khu Keangnam đây các bác? Ngán cơm văn phòng quá rồi.",
        "Cách deal lương khi nhảy việc? Mình đang muốn x30% lương hiện tại.",
        "Đồng nghiệp ngồi cạnh hôi nách quá phải làm sao tế nhị đây ạ? Cứu em!!!",
    ]
    
    pseudonyms = ["Mèo Béo Kế Toán", "Cá Mập Marketing", "Gấu IT", "Thỏ HR", "Sóc Designer", "Cú Đêm Dev"]

    for i in range(20):
        user = random.choice(users) if users else None
        Confession.objects.create(
            title=f"Confession #{i+1}",
            content=random.choice(contents) + " " + fake.sentence(),
            author=user,
            pseudonym=random.choice(pseudonyms),
            is_anonymous=True,
            status='APPROVED' if i % 5 != 0 else 'PENDING', # 80% là đã duyệt
            likes_count=random.randint(0, 500),
            comments_count=random.randint(0, 50),
            created_at=timezone.now() - timedelta(hours=random.randint(1, 48))
        )
    print("✅ Đã tạo 20 Confessions.")

def create_resources(users):
    print("🔄 Đang tạo Kho tài liệu (Zone 1)...")
    DocumentResource.objects.all().delete()
    
    titles = [
        ("Mẫu Slide Báo cáo Tháng đẹp lung linh", "PPT"),
        ("File Excel Tính lương tự động 2024", "XLS"),
        ("Mẫu Hợp đồng lao động song ngữ", "DOC"),
        ("Bộ Vector Icon văn phòng 3D", "VECTOR"),
        ("CV Template cho dân Marketing", "DOC"),
    ]

    for t, f_type in titles:
        DocumentResource.objects.create(
            title=t,
            slug=fake.slug(),
            description="Tải xuống miễn phí, dùng ngay không cần chỉnh sửa nhiều.",
            file_type=f_type,
            uploaded_by=random.choice(users) if users else None,
            download_count=random.randint(100, 2000)
        )
    print("✅ Đã tạo tài liệu mẫu.")

def create_food_reviews():
    print("🔄 Đang tạo Review quán ăn (Zone 2)...")
    FoodReview.objects.all().delete()
    
    reviews = [
        ("Cơm tấm Sà Bì Chưởng", "Quận 1, TP.HCM", 45000),
        ("Bún đậu Mắm tôm Cô Hằng", "Đống Đa, Hà Nội", 35000),
        ("Phở Thìn Lò Đúc", "Hai Bà Trưng, Hà Nội", 90000),
        ("Cà phê Muối Chú Long", "Quận 3, TP.HCM", 25000),
    ]

    for name, addr, price in reviews:
        FoodReview.objects.create(
            title=f"Review {name}",
            slug=fake.slug(),
            location_address=addr,
            avg_price=price,
            rating=random.randint(3, 5),
            views_count=random.randint(50, 500)
        )
    print("✅ Đã tạo review ăn uống.")

def create_products():
    print("🔄 Đang tạo Shop Decor (Zone 4)...")
    Product.objects.all().delete()
    
    products = [
        ("Bàn phím cơ Keychron K2", 1800000, "SHOPEE"),
        ("Ghế Công thái học Ergonomic", 3500000, "LAZADA"),
        ("Đèn màn hình Baseus", 450000, "TIKI"),
        ("Cây để bàn Monstera", 150000, "SHOPEE"),
        ("Kê tay gỗ Óc chó", 250000, "SHOPEE"),
    ]

    for name, price, platform in products:
        Product.objects.create(
            title=name,
            slug=fake.slug(),
            price=price,
            affiliate_link="https://shopee.vn",
            platform=platform
        )
    print("✅ Đã tạo sản phẩm demo.")

def create_rewards():
    print("🔄 Đang tạo Kho quà đổi thưởng...")
    RewardItem.objects.all().delete()
    
    rewards = [
        ("Voucher GotIt 50k", 500),
        ("Thẻ nạp điện thoại 20k", 200),
        ("Ly giữ nhiệt 8Tieng Limited", 1500),
        ("Chuột Logitech Silent", 3000),
    ]
    
    for name, cost in rewards:
        RewardItem.objects.create(
            title=name,
            description="Đổi ngay bằng điểm KPI của bạn.",
            point_cost=cost,
            stock=random.randint(5, 50)
        )
    print("✅ Đã tạo quà đổi thưởng.")

if __name__ == '__main__':
    print("🚀 BẮT ĐẦU TẠO DỮ LIỆU MẪU CHO 8TIENG.VN...")
    create_zones()
    users = create_users()
    create_confessions(users)
    create_resources(users)
    create_food_reviews()
    create_products()
    create_rewards()
    print("✨ HOÀN TẤT! Bây giờ bạn có thể chạy server và kiểm tra.")
    print("   👉 Admin login: admin / admin123")