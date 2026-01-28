from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import os

# --- 0. UTILITIES & ABSTRACT MODELS ---

def get_file_path(instance, filename):
    """Hàm sinh đường dẫn file theo ngày"""
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.slug if hasattr(instance, 'slug') else timezone.now().timestamp(), ext)
    return os.path.join('uploads', timezone.now().strftime('%Y/%m/%d'), filename)

class BaseContent(models.Model):
    """Abstract Model chứa các trường chung"""
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name="URL Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Lượt xem")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# --- 1. USER & GAMIFICATION ---

class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Avatar")
    job_title = models.CharField(max_length=100, blank=True, verbose_name="Chức danh")
    company_name = models.CharField(max_length=100, blank=True, verbose_name="Công ty")
    total_kpi_points = models.IntegerField(default=0, db_index=True, verbose_name="Tổng điểm KPI")
    level_rank = models.CharField(max_length=50, default='Intern', verbose_name="Cấp bậc")

    def __str__(self):
        return self.user.username

class PointHistory(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Điểm danh hàng ngày'),
        ('UPLOAD', 'Tải lên tài liệu'),
        ('POST', 'Viết bài/Review'),
        ('REDEEM', 'Đổi quà'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_histories')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    amount = models.IntegerField(verbose_name="Số điểm (+/-)")
    description = models.CharField(max_length=255, verbose_name="Mô tả chi tiết")
    created_at = models.DateTimeField(auto_now_add=True)

class RewardItem(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tên phần quà")
    description = models.TextField(verbose_name="Mô tả")
    image = models.ImageField(upload_to='rewards/', verbose_name="Ảnh quà")
    point_cost = models.PositiveIntegerField(verbose_name="Điểm cần đổi")
    stock = models.PositiveIntegerField(default=10, verbose_name="Số lượng còn lại")

    def __str__(self):
        return self.title

# --- 2. ZONE 1: PRODUCTIVITY ---

class DocumentResource(BaseContent):
    FILE_TYPES = [
        ('PPT', 'PowerPoint'), ('XLS', 'Excel'),
        ('DOC', 'Word/PDF'), ('VECTOR', 'Design Vector'),
    ]
    description = models.TextField(blank=True, verbose_name="Mô tả tài liệu")
    file_upload = models.FileField(upload_to=get_file_path, verbose_name="File đính kèm")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='DOC')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Người upload")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Lượt tải")

    class Meta:
        verbose_name = "Tài liệu"
        verbose_name_plural = "Kho Tài liệu"

# --- 3. ZONE 2: PANTRY (QUÁN ĂN) & HEALTH ---

class Restaurant(models.Model):
    """Quản lý quán ăn nổi bật"""
    name = models.CharField(max_length=200, verbose_name="Tên quán")
    address = models.CharField(max_length=300, verbose_name="Địa chỉ")
    image = models.ImageField(upload_to='restaurants/', verbose_name="Ảnh đại diện", null=True, blank=True)
    rating = models.FloatField(default=5.0, verbose_name="Điểm đánh giá")
    review_count = models.IntegerField(default=1, verbose_name="Số review")
    category = models.CharField(max_length=100, default="Món ngon", verbose_name="Loại hình")
    url_foody = models.URLField(blank=True, null=True, verbose_name="Link App")

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên món")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="dishes", null=True, blank=True)
    def __str__(self): return self.name

class FoodReview(BaseContent):
    """Review quán ăn trưa (User post)"""
    location_address = models.CharField(max_length=255, verbose_name="Địa chỉ")
    google_map_link = models.URLField(blank=True, verbose_name="Link Google Map")
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    avg_price = models.PositiveIntegerField(verbose_name="Giá trung bình")
    cover_image = models.ImageField(upload_to='food/', verbose_name="Ảnh đại diện")

    class Meta:
        verbose_name = "Review Ăn uống"

class HealthExercise(models.Model):
    """Cấu hình bài tập sức khỏe"""
    EXERCISE_CHOICES = [
        ('yoga', 'Cổ Vai Gáy'), ('wrist', 'Cổ Tay'),
        ('meditation', 'Thiền'), ('music', 'Nhạc Focus'),
    ]
    code = models.CharField(max_length=20, choices=EXERCISE_CHOICES, unique=True, verbose_name="Mã bài tập")
    title = models.CharField(max_length=100, verbose_name="Tên hiển thị")
    youtube_id = models.CharField(max_length=50, verbose_name="ID Youtube")
    duration = models.IntegerField(default=300, verbose_name="Thời gian tập (giây)")

    def __str__(self):
        return self.title

# --- 4. ZONE 3: SOCIAL (CONFESSION) ---

class Confession(BaseContent):
    STATUS_CHOICES = [('PENDING', 'Chờ duyệt'), ('APPROVED', 'Đã duyệt'), ('REJECTED', 'Từ chối')]
    content = models.TextField(verbose_name="Nội dung tâm sự")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    is_anonymous = models.BooleanField(default=True, verbose_name="Chế độ ẩn danh")
    pseudonym = models.CharField(max_length=100, verbose_name="Bút danh hiển thị")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # Reaction Stats
    loves_count = models.PositiveIntegerField(default=0)
    angry_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0) # Legacy field
    comments_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Confession"
        ordering = ['-created_at']

    @property
    def total_reactions(self): return self.loves_count + self.angry_count

class Comment(models.Model):
    post = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Reaction(models.Model):
    REACTION_CHOICES = [('LOVE', 'Yêu thích'), ('ANGRY', 'Phẫn nộ')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('user', 'post')

class Notification(models.Model):
    TYPE_CHOICES = [('SYSTEM', 'Hệ thống'), ('WARNING', 'Cảnh báo'), ('SUCCESS', 'Tin vui')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    content = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class PostReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class HiddenPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_posts')
    post = models.ForeignKey(Confession, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('user', 'post')

# --- 5. ZONE 4: SHOPPING ---

class Product(models.Model):
    is_active = models.BooleanField(default=True, verbose_name="Đang kinh doanh")
    name = models.CharField(max_length=200,null=True, blank=True)
    description = models.TextField(blank=True)
    price_display = models.CharField(max_length=50,null=True, blank=True) # Giá hiển thị (VD: 150.000đ)
    image = models.ImageField(upload_to='shop_decor/')
    affiliate_url = models.URLField(max_length=500, null=True, blank=True)
    category = models.CharField(max_length=100,null=True, blank=True)
    is_hot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    PLATFORM_CHOICES = [
        ('shopee', 'Shopee'),
        ('lazada', 'Lazada'),
        ('tiki', 'Tiki'),
        ('other', 'Khác'),
    ]
    platform = models.CharField(
        max_length=20, 
        choices=PLATFORM_CHOICES, 
        default='shopee',
        verbose_name="Sàn thương mại"
    )
# --- 6. SYSTEM CONFIG ---



class DailyQuote(models.Model):
    TIME_CHOICES = [
        ('morning', 'Buổi Sáng'),
        ('lunch', 'Buổi Trưa'),
        ('work', 'Giờ Làm Việc'),
        ('chill', 'Cuối Ngày/Tối'),
    ]
    content = models.TextField()
    author = models.CharField(max_length=100, default="Sếp ẩn danh")
    time_category = models.CharField(max_length=10, choices=TIME_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self): return f"[{self.time_category}] {self.content[:20]}"