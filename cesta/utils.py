from .models import Cesta, EstadoCesta
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse


def obtener_cesta(request):
    """
    Intenta obtener la cesta ABIERTA del usuario o de la sesión.
    Si no existe una cesta ABIERTA válida, crea una nueva.
    """
    
    # 1. Lógica para usuario autenticado
    if request.user.is_authenticated:
        # Busca la cesta ABIERTA asociada al usuario. Si no existe, crea una nueva.
        cesta, creada = Cesta.objects.get_or_create(
            usuario=request.user, 
            estadoCesta=EstadoCesta.ABIERTA, 
            defaults={'estadoCesta': EstadoCesta.ABIERTA, 'usuario': request.user}
        )
        return cesta
    
    # 2. Lógica para usuario invitado
    else:
        cesta_id = request.session.get('cesta_id')
        cesta = None
        
        if cesta_id:
            try:
                # Busca la cesta por ID de sesión, que esté ABIERTA y sin usuario.
                cesta = Cesta.objects.get(
                    id=cesta_id, 
                    usuario__isnull=True,
                    estadoCesta=EstadoCesta.ABIERTA
                )
            except Cesta.DoesNotExist:
                # Si falla (ID expirado/cesta finalizada), la variable 'cesta' es None
                pass 
        
        if cesta is None:
            # Si no se encontró una cesta ABIERTA válida, crea una nueva.
            cesta = Cesta.objects.create(estadoCesta=EstadoCesta.ABIERTA)
            request.session['cesta_id'] = cesta.id
            request.session.modified = True
            
        return cesta


def enviar_email_confirmacion(pedido, pedido_url):
    # Usar public_id en el asunto
    subject = f"Confirmación de pedido #{pedido.public_id} - Green Garden"

    # Render de plantillas
    text_content = render_to_string(
        "cesta/pedido_confirmado.txt",
        {"pedido": pedido, "pedido_url": pedido_url}
    )

    html_content = render_to_string(
        "cesta/pedido_confirmado.html",
        {"pedido": pedido, "pedido_url": pedido_url}
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        to=[pedido.email_cliente],       # Cambia si tu modelo usa otro campo
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
