from django.test import TestCase, LiveServerTestCase
from unittest.mock import Mock, patch
from django.urls import reverse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from django.contrib.auth import (
    authenticate, 
    login, 
    logout, 
    get_user, 
    SESSION_KEY, 
    BACKEND_SESSION_KEY, 
    HASH_SESSION_KEY
)
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings

from products.models import (
    Category,
    Nutriment,
    Product,
    ProductCategories,
    ProductNutriments,
    ProductUsers,
)
from products.forms import UserCreateForm, LoginForm
from products.management.commands import database_update, database_reset

from io import StringIO

# Homepage page
class HomePageTestCase(TestCase):
    def test_homepage(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)


# Search-result Page
class SearchResultPage(TestCase):
    def setUp(self):
        self.test_product = Product.objects.create(
            name="Produit test", url="test.fr", nutri_score="c"
        )
        self.test_substitute_product = Product.objects.create(
            name="Substitut produit test", url="test-sub.fr", nutri_score="a"
        )
        test_category = Category.objects.create(name="test-category")
        ProductCategories.objects.create(
            product=self.test_product, category=test_category
        )
        ProductCategories.objects.create(
            product=self.test_substitute_product, category=test_category
        )

    # test that Search-result page returns a status code 200, products!=None, searched_product not in products
    # and substitute_product is in products, if product found
    def test_searchresult_page_returns_products_list(self):
        search_string = self.test_product.name
        response = self.client.post(
            reverse("product-search-results"), {"product_name": search_string}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["products"])
        self.assertIn(self.test_substitute_product, response.context["products"])
        self.assertNotIn(self.test_product, response.context["products"])

    # test that Search-result page returns products=None, if product not found
    def test_searchresult_page_returns_none(self):
        search_string = "azerty"
        response = self.client.post(
            reverse("product-search-results"), {"product_name": search_string}
        )
        self.assertIsNone(response.context["products"])

    # test that Search-result page returns context errors, if search-form not valid
    def test_searchresult_form_invalid(self):
        search_string = ""
        response = self.client.post(
            reverse("product-search-results"), {"product_name": search_string}
        )
        self.assertIsNotNone(response.context["errors"])

    # test that Search-result page returns filled saved_product list, if user is_authenticated and has saved product
    def test_searchresult_page_returns_filled_saved_product_list(self):
        test_user = User.objects.create_user(username="testuser", password="test123+")
        self.client.login(username="testuser", password="test123+")
        ProductUsers.objects.create(product=self.test_product, user=test_user)
        ProductUsers.objects.create(
            product=self.test_substitute_product, user=test_user
        )

        search_string = self.test_product.name
        response = self.client.post(
            reverse("product-search-results"), {"product_name": search_string}
        )
        self.assertIsNotNone(response.context["saved_product"])
        self.assertGreater(len(response.context["saved_product"]), 0)


# Product-details page
class ProductDetailsPage(TestCase):
    def setUp(self):
        self.test_product = Product.objects.create(
            name="Produit test", url="test.fr", nutri_score="c"
        )
        self.test_nutriment = Nutriment.objects.create(name="salt", unit="g")
        ProductNutriments.objects.create(
            product=self.test_product, nutriment=self.test_nutriment, quantity=1.5
        )

    # test that Product-Details page returns a status code 200 and the right product with the righ nutriment list,
    # if product exist
    def test_searchresult_page_returns_200(self):
        product_id = self.test_product.id
        response = self.client.get(reverse("product-details", args=(product_id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searched_product"], self.test_product)
        self.assertGreater(len(response.context["product_nutriments"]), 0)
        self.assertEqual(response.context["product_nutriments"][0]["name"], "sel")
        self.assertEqual(response.context["product_nutriments"][0]["unit"], "g")
        self.assertEqual(response.context["product_nutriments"][0]["quantity"], 1.5)

    # test that Product-Details page returns a status code 404, if product doesn't exist
    def test_searchresult_page_returns_404(self):
        product_id = self.test_product.id + 1
        response = self.client.get(reverse("product-details", args=(product_id,)))
        self.assertEqual(response.status_code, 404)


# Product save
class ProductSave(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+"
        )
        self.test_product = Product.objects.create(
            name="Produit test", url="test.fr", nutri_score="a"
        )
        self.client.login(username="testuser", password="test123+")

    # test that Save-product will create a relation user-product and return appropriate JSON, if the product is not already saved
    def test_product_save(self):
        expected_json = {
            "saved": True,
            "product_name": self.test_product.name,
            "response": "ajouté à vos favoris",
        }
        response = self.client.get(
            reverse("save-product", args=(self.test_product.id,))
        )
        product_saved = ProductUsers.objects.filter(
            product=self.test_product.id, user=self.test_user.id
        ).exists()

        self.assertJSONEqual(response.content, expected_json)
        self.assertTrue(product_saved)

    # test that Save-product will delete a relation user-product and return appropriate JSON, if the product is already saved
    def test_product_unsave(self):
        expected_json = {
            "saved": False,
            "product_name": self.test_product.name,
            "response": "retiré de vos favoris",
        }
        ProductUsers.objects.create(product=self.test_product, user=self.test_user)
        response = self.client.get(
            reverse("save-product", args=(self.test_product.id,))
        )
        product_saved = ProductUsers.objects.filter(
            product=self.test_product.id, user=self.test_user.id
        ).exists()

        self.assertJSONEqual(response.content, expected_json)
        self.assertFalse(product_saved)


# User-create page
class UserCreatePage(TestCase):
    def setUp(self):
        self.test_create_form = UserCreateForm()

    # test that User-Create page returns a status code 200 and the right form, on get request
    def test_usercreate_page_get_returns_form(self):
        response = self.client.get(reverse("user-create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].fields.keys(), self.test_create_form.fields.keys()
        )

    # test that User-Create page create a new user, authenticate it and redirect to homepage, on post request with valid form
    def test_usercreate_page_post_valid_form(self):
        response = self.client.post(
            reverse("user-create"),
            {
                "username": "testuser",
                "first_name": "testuser name",
                "email": "test@test.fr",
                "password1": "test123+",
                "password2": "test123+",
            },
        )
        last_created_user = User.objects.latest("id")

        self.assertEqual(last_created_user.username, "testuser")
        self.assertEqual(
            last_created_user.id, int(self.client.session["_auth_user_id"])
        )
        self.assertRedirects(response=response, expected_url="/products/")
        self.assertTemplateUsed(template_name="products/homepage.html")

    # test that User-Create page returns errors context, on post request with invalid form
    def test_usercreate_page_post_invalid_form_weak_password(self):
        response = self.client.post(
            reverse("user-create"),
            {
                "username": "testuserfail",
                "first_name": "testuser name",
                "email": "testeur@test.fr",
                "password1": "123456",
                "password2": "123456",
            },
        )
        self.assertIsNotNone(response.context["errors"])

    # test that User-Create page returns errors context, on post request with invalid form with email already existing
    def test_usercreate_page_form_raise_validation_error_on_email(self):
        User.objects.create_user(
            username="testi", password="test123+", email="test@test.fr"
        )
        form_params = {
            "username": "testo",
            "first_name": "testuser name",
            "email": "test@test.fr",
            "password1": "test123+",
            "password2": "test123+",
        }
        form = UserCreateForm(form_params)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("email", "email"))


# User-login page
class UserLoginPage(TestCase):
    def setUp(self):
        self.test_login_form = LoginForm()
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+"
        )

    # test that User-login page returns a status code 200 and the right form, on get request
    def test_userlogin_page_get_returns_form(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].fields.keys(), self.test_login_form.fields.keys()
        )

    # test that User-login page log user in and redirect to homepage, on post request with good credentials
    def test_userlogin_page_post_valid_credentials(self):
        self.client.session["_auth_user_id"] = ""
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "test123+"}
        )
        self.assertEqual(self.test_user.id, int(self.client.session["_auth_user_id"]))
        self.assertRedirects(response=response, expected_url="/")
        self.assertTemplateUsed(template_name="products/homepage.html")

    # test that User-login page return errors context, on post request with bad credentials
    def test_userlogin_page_post_invalid_credentials(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "test123"}
        )

        self.assertIsNotNone(response.context["form"].errors)
        self.assertFalse(response.context["user"].is_authenticated)


# User-logout view
class UserLogoutView(TestCase):
    # test that User-logout view redirect to home page
    def test_userlogout_view(self):
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response=response, expected_url="/products/")


# User-result Page
class UserResultPage(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+"
        )
        self.test_product = Product.objects.create(
            name="Produit test", url="test.fr", nutri_score="a"
        )
        self.client.login(username="testuser", password="test123+")

    # test that User-result page returns a status code 200 and a filled product list if user has saved products
    def test_userresult_page_returns_200_with_products(self):
        ProductUsers.objects.create(product=self.test_product, user=self.test_user)
        response = self.client.get(reverse("product-user-results"))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context["products"]), 0)

    # test that User-result page returns a status code 200 and an empty product list if user has no saved products
    def test_userresult_page_returns_200_without_products(self):
        response = self.client.get(reverse("product-user-results"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["products"]), 0)


# User-details page
class UserDetailsPage(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+", email="test@test.fr"
        )
        self.client.login(username="testuser", password="test123+")

    # test that User-details page returns a status code 200 and the template show user's infos
    def test_userdetails_page_returns_200_with_user_infos(self):
        response = self.client.get(reverse("user"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testuser")
        self.assertEqual(response.context["user"].email, "test@test.fr")


# Models
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


# Custom manage.py command database_update
class CommandTest(TestCase):
    @patch('products.management.commands.database_update.Command.openfoodfacts_api_get_product')
    def test_custom_command_database_update(self, mock_get):
        product = [{
            'url': 'https://url.test.com',
            'product_name': "produit test mock",
            'nutrition_grades_tags': ["c",],
            'categories_tags': ['test',],
        }]

        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = product
        
        response = database_update.Command.openfoodfacts_api_get_product(self, category="test", number_of_products=1, user_agent="test-agent")
        
        self.assertIsNotNone(response)
        self.assertTrue(mock_get.called)

    def tex_custom_commend_database_reset(self):
        self.test_product = Product.objects.create(
            name="Produit test 2", url="test.fr", nutri_score="c"
        )
        self.test_nutriment = Nutriment.objects.create(name="salt", unit="g")
        ProductNutriments.objects.create(
            product=self.test_product, nutriment=self.test_nutriment, quantity=1.5
        )
        
        self.assertIsNotNone(Product.objects.get(id=self.test_product.id))

        database_reset.Command.handle(self)

        self.assertIsNone(Product.objects.get(id=self.test_product.id))


# User action test using Selenium
class UserLoginLogoutSeleniumTest(LiveServerTestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username="testuser", password="test123+", email="test@test.fr"
        )
        self.selenium = webdriver.Firefox()
        super(UserLoginLogoutSeleniumTest, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(UserLoginLogoutSeleniumTest, self).tearDown()

    def test_selenium_login(self):
        selenium = self.selenium

        selenium.get('%s%s' % (self.live_server_url, '/products/user/login/'))
        username = selenium.find_element_by_id('id_username')
        pwd = selenium.find_element_by_id('id_password')

        login_submit = selenium.find_element_by_id('user-login-button')

        username.send_keys('testuser')
        pwd.send_keys('test123+')

        login_submit.send_keys(Keys.RETURN)

        cookies = selenium.get_cookies()

        self.assertTrue(len(cookies) > 0)

    def test_selenium_user_view(self):
        session_cookie = self.create_session()

        selenium = self.selenium
        selenium.get(self.live_server_url)

        selenium.add_cookie(session_cookie)
        selenium.refresh()

        selenium.get('%s%s' % (self.live_server_url, '/products/user/'))

        self.assertIsNotNone(selenium.get_cookie('sessionid'))
        self.assertIn('Votre identifiant : testuser', selenium.page_source)

    def test_selenium_user_logout(self):
        session_cookie = self.create_session()

        selenium = self.selenium
        selenium.get(self.live_server_url)

        selenium.add_cookie(session_cookie)
        selenium.refresh()

        self.assertIsNotNone(selenium.get_cookie('sessionid'))

        selenium.get('%s%s' % (self.live_server_url, '/products/user/logout/'))

        self.assertIsNone(selenium.get_cookie('sessionid'))

    def create_session(self):
        session = SessionStore()
        session[SESSION_KEY] = self.test_user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = self.test_user.get_session_auth_hash()
        session.save()

        cookie = {
            'name': settings.SESSION_COOKIE_NAME,
            'value': session.session_key,
            'secure': False,
            'path': '/',
        }

        return cookie
