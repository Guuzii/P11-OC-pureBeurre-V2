from django.urls import include, path
from django.contrib.auth import views as auth_views

from . import views
from products.views import HomeView

urlpatterns = [
    path("<int:product_id>", views.Comments.as_view(), name="post-comment"),
]
