from django.db import models

class Brand(models.Model):
    name= models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name=models.CharField(max_length=200)
    brand=models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",

    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",

    )

    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    layout = models.CharField(max_length=30, blank= True)
    connection_type = models.CharField(max_length=50, blank=True)
    image= models.ImageField(
        upload_to="products/",
        blank=True,
    )
    is_available= models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.name} {self.name}"