from django.shortcuts import render, redirect
from django.contrib import messages

from products.views import ProductDetails
from products.models import Product

from .models import Comment
from .forms import CommentForm

from django.contrib.auth.models import User

# Create your views here.
class Comments(ProductDetails):
    def post(self, request, product_id):
        form = CommentForm(request.POST)

        if request.user.is_authenticated and form.is_valid():
            user = request.user
            product = Product.objects.get(id=product_id)
            message = form.cleaned_data['message']

            new_comment = Comment(user=user, product=product, message=message)
            new_comment.save()
            
            messages.info(request, "Votre commentaire a bien été envoyé. Il devra être validé par un administrateur avant de s'afficher.")
            
            return redirect('product-details', product_id=product_id)

        messages.info(request, "Votre commentaire n'a pas été envoyé car il était vide.")

        return redirect('product-details', product_id=product_id)