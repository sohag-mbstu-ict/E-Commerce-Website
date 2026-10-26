from django.urls import path

from .views import page_detail

app_name = 'pages'

urlpatterns = [
    path('<slug:slug>/', page_detail, name='detail'),
]
