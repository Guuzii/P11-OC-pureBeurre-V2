from django import forms
from django.forms import ModelForm, TextInput, EmailInput
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

from .models import Comment

class CommentForm(forms.ModelForm):
    
    class Meta:
        model = Comment
        fields = ('message',)
        widgets = {
            'message': forms.Textarea(attrs={'cols': 60, 'rows': 5})
        }