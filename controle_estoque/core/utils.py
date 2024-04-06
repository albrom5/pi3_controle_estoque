from ninja.errors import AuthenticationError

from controle_estoque.core.models import Perfil


def valida_permissao_empresa(usuario, empresa):
    if usuario.is_superuser:
        return
    
    perfis_usuario = Perfil.objects.filter(
        usuario=usuario,
        empresa=empresa
    ).exists()
    if not perfis_usuario:
        raise AuthenticationError()
