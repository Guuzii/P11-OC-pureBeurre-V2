from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import authenticate, login, logout, get_user
from django.contrib.auth.models import User

from products.models import Product

from comments.models import Comment

# Create your tests here.

# test models
class ModelsTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+", email="test@test.fr"
        )
        self.test_product = Product.objects.create(
            name="Produit test", url="test.fr", nutri_score="a"
        )
        self.test_comment = Comment.objects.create(
            user=self.test_user, product=self.test_product, message="test comment Comment Model"
        )

    # test that Comment model return self.message
    def test__models_returns_self_name(self):
        self.assertEqual(str(self.test_comment), self.test_comment.message)
        self.assertEqual(str(self.test_comment.product), self.test_product.name)


# test Comments display on productDetailsPage
class ProductDetailsPageComments(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+", email="test@test.fr"
        )
        self.test_product = Product.objects.create(
            name="Produit test 2", url="test.fr", nutri_score="1"
        )
        self.test_comment = Comment.objects.create(
            user=self.test_user, product=self.test_product, message="test comment productDetailsPage"
        )

    # test comments and form is displayed when user is authenticated
    def test_comments_displayed_logged_in(self):
        self.client.login(username="testuser", password="test123+")
        product_id = self.test_product.id
        user = get_user(self.client)
        response = self.client.get(reverse("product-details", args=(product_id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searched_product"], self.test_product)
        self.assertTrue(user.is_authenticated)
        self.assertIsNotNone(response.context["comment_form"])
        self.assertIsNotNone(response.context["comments"])

    def test_comments_not_displayed_logged_out(self):
        self.client.logout()
        product_id = self.test_product.id
        user = get_user(self.client)
        response = self.client.get(reverse("product-details", args=(product_id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searched_product"], self.test_product)
        self.assertFalse(user.is_authenticated)
        self.assertIsNone(response.context["comment_form"])
        self.assertIsNone(response.context["comments"])

        
# test post comment selenium