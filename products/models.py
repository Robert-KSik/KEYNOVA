from django.db import models
from django.utils.text import slugify 

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this brand as a quick chip on the home page.",
    )
    featured_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Chip order on the home page. 1 appears first.",
    )

    class Meta:
        ordering = ["featured_order", "name"]

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.name)
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.ForeignKey(
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
    layout = models.CharField(max_length=30, blank=True)
    connection_type = models.CharField(max_length=50, blank=True)
    image = models.ImageField(
        upload_to="products/",
        blank=True,
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    warranty_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Leave blank if there is no warranty.",
    )

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    def grouped_specs(self):
        specs = list(self.specs.all())
        groups = []
        for key, label in ProductSpec.GROUPS:
            rows = [s for s in specs if s.group == key]
            if rows:
                groups.append({"label": label, "rows": rows})
        return groups

class ProductVariant(models.Model):
    SWITCH_TYPES = [
        ("linear", "Linear"),
        ("tactile", "Tactile"),
        ("clicky", "Clicky"),
        ("hall effect", "Hall Effect"),
        ("tmr magnetic", "TMR Magnetic"),
        ("optical", "Optical"),
        
       
    ]

    KEYCAP_MATERIALS = [
        ("PBT", "PBT"),
        ("ABS", "ABS"),
        ("PC", "PC"),
        ("POM", "POM"),
        ("Ceramic", "Ceramic"),
        ("Metal", "Metal"),
        ("Exact material unconfirmed", "Exact material unconfirmed"),

    ]

    CONNECTION_TYPES = [
        ("USB-C", "USB-C"),
        ("Bluetooth", "Bluetooth"),
        ("2.4GHz", "2.4 GHz Wireless"),
        ("Tri-mode", "Tri-mode"),
    ]

    LAYOUT_CHOICES = [
        ("60%", "60%"),
        ("65%", "65%"),
        ("75%", "75%"),
        ("TKL", "Tenkeyless"),
        ("Full-size", "Full-size"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    variant_name = models.CharField(max_length=150)

    image = models.ImageField(
        upload_to="products/variants/",
        blank=True,
    )

    case_color = models.CharField(max_length=50)
    keycap_color = models.CharField(max_length=50)

    keycap_material = models.CharField(
        max_length=40,
        choices=KEYCAP_MATERIALS,
        default="PBT",
    )

    switch_type = models.CharField(
        max_length=20,
        choices=SWITCH_TYPES,
    )
    switch_model = models.CharField(max_length=100, blank=True)

    connection_type = models.CharField(
        max_length=20,
        choices=CONNECTION_TYPES,
    )

    layout = models.CharField(
        max_length=20,
        choices=LAYOUT_CHOICES,
    )

    battery_capacity_mah = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Battery capacity in mAh; leave blank for wired models.",
    )

    price_adjustment = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Extra cost or discount relative to the base product price.",
    )

    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original variant price before discount. Leave blank when not on sale.",
)

    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["product", "variant_name"]

    def __str__(self):
        return f"{self.product.name} — {self.variant_name}"

    @property
    def effective_price(self):
        return self.product.price + self.price_adjustment

    
    @property
    def sale_price(self):
        return self.effective_price

    @property
    def discount_amount(self):
        if (
            self.compare_at_price is not None
            and self.compare_at_price > self.sale_price
        ):
            return self.compare_at_price - self.sale_price
        return 0

    @property
    def discount_percentage(self):
        if (
            self.compare_at_price is not None
            and self.compare_at_price > self.sale_price
        ):
            return round(
                (self.discount_amount / self.compare_at_price) * 100
            )
        return 0

    @property
    def is_on_sale(self):
        return self.discount_percentage > 0


class VariantOption(models.Model):
    OPTION_TYPES = [
        ("switch", "Switch"),
        ("case_color", "Case Color"),
        ("keycap_color", "Keycap Color"),
        ("keycap_material", "Keycap Material"),
        ("connection", "Connection"),
    ]

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="options",
    )
    option_type = models.CharField(
        max_length=30,
        choices=OPTION_TYPES,
    )
    choice_name = models.CharField(max_length=100)
    extra_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["option_type", "choice_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "option_type", "choice_name"],
                name="unique_variant_option_choice",
            )
        ]

    def __str__(self):
        return f"{self.variant} — {self.choice_name}"

class ProductSpec(models.Model):
    GROUPS = [
        ("build", "Layout and build"),
        ("performance", "Performance"),
        ("connectivity", "Connectivity and battery"),
        ("compatibility", "Compatibility"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="specs"
    )
    group = models.CharField(max_length=20, choices=GROUPS, default="build")
    name = models.CharField(max_length=80)
    value = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.product.name}: {self.name}"