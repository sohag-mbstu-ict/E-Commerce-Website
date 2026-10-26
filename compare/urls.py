from django.urls import path

from . import views

app_name = 'compare'

urlpatterns = [
    path('', views.compare_view, name='view'),
    path('add/<int:product_id>/', views.compare_add, name='add'),
    path('remove/<int:product_id>/', views.compare_remove, name='remove'),
    path('clear/', views.compare_clear, name='clear'),
]
