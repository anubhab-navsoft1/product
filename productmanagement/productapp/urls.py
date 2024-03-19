from django.contrib import admin
from django.urls import path
from dev_anubhab import views

urlpatterns = [
    path('get/', views.GetAllApi.as_view(), name = 'add_all'),
    path('add/', views.CreateAllProductModelView.as_view(), name = 'add_all'),
    path('update_products/<uuid:product_id>/', views.UpdateProductsView.as_view(), name='update_products'),
    path('delete/<uuid:product_id>/', views.DeleteProductView.as_view(), name='delete_product'),
    path('delete-all/', views.DeleteAllItemsView.as_view(), name='delete_all_items')
 ]