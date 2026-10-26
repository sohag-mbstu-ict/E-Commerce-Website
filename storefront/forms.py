from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from orders.models import Order
from reviews.models import Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False, max_length=20)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address_line', 'city', 'postal_code', 'country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField(required=False)
    address_line = forms.CharField(max_length=255, widget=forms.Textarea(attrs={'rows': 2}))
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20, required=False)
    country = forms.CharField(max_length=100, initial='Bangladesh')
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    payment_method = forms.ChoiceField(choices=Order.PaymentMethod.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['payment_method'].widget.attrs['class'] = 'form-select'


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} star{"s" if i > 1 else ""}') for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['rating'].widget.attrs['class'] = 'form-select'
