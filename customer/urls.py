from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload-file'),
    path('supplier/', views.save_supplier, name='supplier-save'),
    path('supplier/delete/', views.delete_supplier, name='supplier-delete'),
    path('service_note/', views.save_service_note, name='service-note-save'),
    path('service_note/delete/', views.delete_service_note,
         name='service-note-delete'),
    path('app-data/', views.update_app_data, name='app-data'),
    path('requirement/', views.requirement, name='requirement'),
    path('customer/', views.customer_list, name='customer-list'),
    path('customer/<int:pk>', views.customer_view, name='customer-view'),
    path('customer/search', views.customer_search, name='customer-search'),
    path('deposit/', views.deposit_list, name='deposit-list'),
    path('deposit/search', views.deposit_search, name='deposit-search'),
    path('deposit/<int:pk>', views.deposit_view, name='deposit-view'),
    path('on-file/', views.on_file_list, name='on-file-list'),
    path('on-file/search', views.on_file_search, name='on-file-search'),
    path('on-file/<int:pk>', views.on_file_view, name='on-file-view'),
    path('order/', views.order_list, name='order-list'),
    path('order/search', views.order_search, name='order-search'),
    path('order/<int:pk>', views.order_view, name='order-view'),
    path('installation/', views.installation_list, name='installation-list'),
    path('installation/search', views.installation_search, name='installation-search'),
    path('installation/<int:pk>', views.installation_view,
         name='installation-view'),
    path('account/', views.account_list, name='account-list'),
    path('account/search', views.account_search, name='account-search'),
    path('account/<int:pk>', views.account_view, name='account-view'),
    path('service/', views.service_list, name='service-list'),
    path('service/search', views.service_list, name='service-search'),
    path('service/<int:pk>', views.service_view, name='service-view'),
    path('finished/', views.finished_list, name='finished-list'),
    path('finished/search', views.finished_search, name='finished-search'),
    path('finished/<int:pk>', views.finished_view, name='finished-view'),
    path('setupScraping/', views.setupScraping, name='setupScraping-list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
