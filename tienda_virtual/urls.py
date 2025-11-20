"""
URL configuration for tienda_virtual project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from home import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.index, name='inicio'),                # Página principal (Escaparate)
    path('catalogo/', views.catalogo, name='catalogo'),  # Nueva página Catálogo
    path('admin/', admin.site.urls),
    path('', include('productos.urls')),
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),
    path('cesta/', include('cesta.urls')),  # URLs de la aplicación cesta
    path('cesta/', include(('cesta.urls', 'cesta'), namespace='cesta')),
    # Pantalla de información de la empresa (usa `home.views.company_info`)
    path('company/', views.company_info, name='company_info')

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)