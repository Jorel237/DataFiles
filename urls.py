from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet,
    VehicleViewSet,
    PolicyViewSet,
    InsurerViewSet,
    InsuranceProductViewSet,
    CertificateTemplateViewSet,
)


router = DefaultRouter()
router.register('customers', CustomerViewSet, basename='customer')
router.register('vehicles', VehicleViewSet, basename='vehicle')
router.register('policies', PolicyViewSet, basename='policy')
router.register('insurers', InsurerViewSet, basename='insurer')
router.register('products', InsuranceProductViewSet, basename='product')
router.register('certificate-templates', CertificateTemplateViewSet, basename='certificate-template')

urlpatterns = [
    path('', include(router.urls)),
]

