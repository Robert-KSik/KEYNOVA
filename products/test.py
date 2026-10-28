
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Brand, Category, Product


class ProductAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.brand = Brand.objects.create(
            name="Test Keyboard Brand",
            description="Brand created for automated testing.",
        )

        self.category = Category.objects.create(
            name="Test Keyboards",
            description="Category created for automated testing.",
        )

        self.product = Product.objects.create(
            name="Test Mechanical Keyboard",
            brand=self.brand,
            category=self.category,
            description="A keyboard used for API tests.",
            price=Decimal("89.99"),
            stock=10,
            layout="75%",
            connection_type="USB-C",
            is_available=True,
        )

    def test_product_list_endpoint_returns_200(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)

    def test_product_list_returns_json(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Content-Type"].split(";")[0],
            "application/json",
        )

    def test_product_detail_returns_404_for_missing_product(self):
        response = self.client.get("/api/products/999999/")

        self.assertEqual(response.status_code, 404)

    def test_product_list_contains_created_product(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)

        product_names = [
            item["name"] for item in response.data
        ]

        self.assertIn(self.product.name, product_names)

    def test_product_detail_returns_correct_product(self):
        response = self.client.get(
            f"/api/products/{self.product.pk}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], self.product.name)
        self.assertEqual(
            Decimal(str(response.data["price"])),
            Decimal("89.99"),
        )
