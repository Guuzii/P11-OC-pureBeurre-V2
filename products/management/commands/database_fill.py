from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from products.models import (
    Nutriment,
    Category,
    Product,
    ProductCategories,
    ProductNutriments,
)

import json
import requests


class Command(BaseCommand):
    help = "Call Open Food Facts API to get products and fill the database"

    def handle(self, *args, **options):

        Product.objects.all().delete()
        Nutriment.objects.all().delete()
        Category.objects.all().delete()

        for nutriment in settings.NUTRIMENTS:
            new_nutriment = Nutriment(
                name=nutriment, unit=settings.NUTRIMENTS[nutriment]["unit"]
            )
            new_nutriment.save()

        for category in settings.PRODUCTS_CATEGORIES:
            new_category = Category(name=category)
            new_category.save()

        for category in settings.PRODUCTS_CATEGORIES:
            self.get_products_for_category(category)

        self.stdout.write("PRODUCTS DATAS IMPORTATION DONE")

    def get_products_for_category(self, product_category: str):
        """
            GET request to open food fact api to get products in a category.
            For each response, datas are inserted in the database

            Parameters:
                - product_category (str): the name of the category of products to get
        """

        response = self.openfoodfacts_api_get_product(product_category, settings.NB_PRODUCTS_TO_GET, settings.USER_AGENT_OFF)

        for product in response["products"]:

            new_product = Product()
            new_product.url = product["url"]

            # set the image_url of the product
            if "image_url" in product:
                new_product.image_url = product["image_url"]

            # set the name of the product
            if "product_name" in product:
                if (
                    product["product_name"] is not None
                    and product["product_name"] is not ""
                ):
                    new_product.name = product["product_name"]
                else:
                    if (
                        product["product_name_fr"] is not None
                        and product["product_name_fr"] is not ""
                    ):
                        new_product.name = product["product_name_fr"]
                    else:
                        continue
            else:
                continue

            # check if product exist in database
            if Product.objects.filter(name__iexact=new_product.name):
                continue

            # set the nutrition score of the product
            if "nutrition_grades_tags" in product:
                if product["nutrition_grades_tags"][0].lower() not in [
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                ]:
                    new_product.nutri_score = "e"
                else:
                    new_product.nutri_score = product["nutrition_grades_tags"][
                        0
                    ].lower()

            new_product.save()

            # create the relations product-category
            if len(product["categories_tags"]) > 0:
                for category in product["categories_tags"]:
                    # parsing of the category tag
                    new_category = category.replace("en:", "")
                    new_category = new_category.replace("fr:", "")

                    if new_category in settings.PRODUCTS_CATEGORIES:
                        new_product_category = Category.objects.get(name=new_category)
                        new_product.categories.add(new_product_category)
                    else:
                        continue
            else:
                continue

            # create the relations product-nutriment for every nutriments specified in settings
            for nutriment in settings.NUTRIMENTS:
                new_nutriment = Nutriment.objects.get(name=nutriment)

                if nutriment + "_100g" in product["nutriments"]:
                    if product["nutriments"][nutriment + "_100g"] is not "":
                        new_product.nutriments.add(
                            new_nutriment,
                            through_defaults={
                                "quantity": product["nutriments"][nutriment + "_100g"]
                            },
                        )
                    else:
                        new_product.nutriments.add(new_nutriment)
                else:
                    new_product.nutriments.add(new_nutriment)


    def openfoodfacts_api_get_product(self, category: str, number_of_products: int, user_agent):
        request = requests.get(
            "https://fr-en.openfoodfacts.org/cgi/search.pl?search_terms="
            + category
            + "&page_size="
            + str(number_of_products)
            + "&action=process&json=1",
            headers={"items": user_agent},
        )

        return json.loads(request.text)
