from django.test import TestCase

# Create your tests here.

class ModelsTest(TestCase):
    def setUp(self):
        self.test_product = Product.objects.create(
            name="Produit test", url="test.fr", nutri_score="a"
        )
        self.test_category = Category.objects.create(name="test-category")
        self.test_nutriment = Nutriment.objects.create(name="testNutriment", unit="g")

    # test that Product model return self.name
    def test__models_returns_self_name(self):
        self.assertEqual(str(self.test_product), self.test_product.name)
        self.assertEqual(str(self.test_category), self.test_category.name)
        self.assertEqual(str(self.test_nutriment), self.test_nutriment.name)

# test view
# test post comment selenium