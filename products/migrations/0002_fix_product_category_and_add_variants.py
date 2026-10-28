
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="Category",
            new_name="category",
        ),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                to="products.category",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
            ),
        ),
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("variant_name", models.CharField(max_length=150)),
                ("case_color", models.CharField(max_length=50)),
                ("keycap_color", models.CharField(max_length=50)),
                (
                    "keycap_material",
                    models.CharField(
                        choices=[("PBT", "PBT"), ("ABS", "ABS")],
                        default="PBT",
                        max_length=10,
                    ),
                ),
                (
                    "switch_type",
                    models.CharField(
                        choices=[
                            ("linear", "Linear"),
                            ("tactile", "Tactile"),
                            ("clicky", "Clicky"),
                        ],
                        max_length=20,
                    ),
                ),
                ("switch_model", models.CharField(blank=True, max_length=100)),
                (
                    "connection_type",
                    models.CharField(
                        choices=[
                            ("USB-C", "USB-C"),
                            ("Bluetooth", "Bluetooth"),
                            ("2.4GHz", "2.4 GHz Wireless"),
                            ("Tri-mode", "Tri-mode"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "layout",
                    models.CharField(
                        choices=[
                            ("60%", "60%"),
                            ("65%", "65%"),
                            ("75%", "75%"),
                            ("TKL", "Tenkeyless"),
                            ("Full-size", "Full-size"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "battery_capacity_mah",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Battery capacity in mAh; leave blank for wired models.",
                        null=True,
                    ),
                ),
                (
                    "price_adjustment",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Extra cost or discount relative to the base product price.",
                        max_digits=8,
                    ),
                ),
                ("stock", models.PositiveIntegerField(default=0)),
                ("is_available", models.BooleanField(default=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "ordering": ["product", "variant_name"],
            },
        ),
    ]
