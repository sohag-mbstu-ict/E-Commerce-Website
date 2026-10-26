from django.urls import path

from .views import RecentOrdersView, SalesSummaryView

app_name = 'dashboard'

urlpatterns = [
    path('summary/', SalesSummaryView.as_view(), name='summary'),
    path('recent-orders/', RecentOrdersView.as_view(), name='recent-orders'),
]
