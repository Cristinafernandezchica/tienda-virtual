from .models import ContactInfo

def company_info_context(request):
    contact_info = ContactInfo.objects.first()
    return {"contact_info": contact_info}
