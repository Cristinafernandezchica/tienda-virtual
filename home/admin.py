from django.contrib import admin
from .models import Producto, Escaparate, ContactInfo

# Register your models here.

admin.site.register(Producto)
admin.site.register(Escaparate)


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'email', 'telefono', 'active', 'updated_at')
	list_filter = ('active',)
	search_fields = ('nombre', 'email', 'direccion')
	readonly_fields = ('updated_at',)

	def save_model(self, request, obj, form, change):
		"""Si marcamos este objeto como activo, desactivar los demás.

		Esto garantiza que solo haya un `ContactInfo` activo mostrado en la web.
		"""
		if obj.active:
			# desactivar otros objetos
			ContactInfo.objects.exclude(pk=obj.pk).update(active=False)
		super().save_model(request, obj, form, change)