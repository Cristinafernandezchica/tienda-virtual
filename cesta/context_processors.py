from cesta.utils import obtener_cesta

def resumen_cesta(request):
    try:
        cesta = obtener_cesta(request)
        return {'cesta_resumen': cesta}
    except Exception:
        return {'cesta_resumen': None}
