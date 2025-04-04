from django.urls import path

from api.views import ProductMaterialsAPIView

urlpatterns = [
    path('materials/', ProductMaterialsAPIView.as_view(), name='product-materials'),
]