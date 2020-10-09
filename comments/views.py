from django.shortcuts import render, redirect
from products.views import ProductDetails

from .models import Comment
from .forms import CommentForm

# Create your views here.
class Comments(ProductDetails):
    def post(self, request, product_id):
        print('POST COMMENTS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        print(request.POST)

        return redirect('product-details', product_id=product_id)