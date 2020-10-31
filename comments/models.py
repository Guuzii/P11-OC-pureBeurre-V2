from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

# Create your models here.
class Comment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comment"
    )
    date = models.DateTimeField("Date création", auto_now=False, auto_now_add=True)
    message = models.TextField("Message")
    is_validated = models.BooleanField("Validé par admin", default=False)

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ["date"]

    def __str__(self):
        return self.message
