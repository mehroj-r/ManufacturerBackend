from django.urls import path

from api.views import ProductMaterialsAPiView

urlpatterns = [
    path('materials/', ProductMaterialsAPiView.as_view(), name='product-materials'),
]