from django.shortcuts import get_object_or_404
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from controle_estoque.core import models, schemas
from controle_estoque.core.utils import valida_permissao_empresa

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)


@api.post('/armazem/novo', auth=JWTAuth(), response=schemas.ArmazemSchema)
def armazem_novo(request, payload: schemas.ArmazemNovoSchema):
    empresa = models.Empresa.objects.filter(uuid=payload.empresa_id).first()
    valida_permissao_empresa(request.user, empresa)

    armazem = models.Armazem(**payload.dict())
    armazem.save()
    return armazem


@api.get('/armazem/{armazem_id}', auth=JWTAuth(), response=schemas.ArmazemSchema)
def armazem(request, armazem_id: str):
    armazem = get_object_or_404(models.Armazem, uuid=armazem_id)
    valida_permissao_empresa(request.user, armazem.empresa)
    return armazem


@api.patch('/armazem/{armazem_id}', auth=JWTAuth(), response=schemas.ArmazemSchema)
def armazem_edita(request, armazem_id: str, payload: schemas.ArmazemEditaSchema):
    armazem = get_object_or_404(models.Armazem, uuid=armazem_id)
    valida_permissao_empresa(request.user, armazem.empresa)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(armazem, attr, value)
    armazem.save()
    return armazem


@api.delete('/armazem/{armazem_id}', auth=JWTAuth())
def armazem_exclui(request, armazem_id: str):
    armazem = get_object_or_404(models.Armazem, uuid=armazem_id)
    valida_permissao_empresa(request.user, armazem.empresa)
    uuid_str = armazem.uuid
    armazem.delete()
    return {'successo': f'O armazém {armazem.nome} - {uuid_str} foi excluído.'}


@api.get('/armazens', auth=JWTAuth(), response=list[schemas.ArmazemSchema])
def armazem_lista(request, empresa_id: str | None = None):
    armazens = models.Armazem.objects.select_related(
        'empresa', 'municipio'
    ).order_by('nome')
    if empresa_id is not None:
        empresa = models.Empresa.objects.filter(uuid=empresa_id).first()
        valida_permissao_empresa(request.user, empresa)
        armazens = armazens.filter(empresa=empresa)
        return armazens

    if request.user.is_superuser:
        return armazens
    
    armazens = armazens.filter(empresa__perfil__usuario=request.user).distinct()
    return armazens


@api.post('/produto/novo', auth=JWTAuth(), response=schemas.ProdutoSchema)
def produto_novo(request, payload: schemas.ProdutoNovoSchema):
    produto = models.Produto(**payload.dict())
    produto.save()
    return produto


@api.get('/produto/{produto_id}', auth=JWTAuth(), response=schemas.ProdutoSchema)
def produto(request, produto_id: str):
    produto = get_object_or_404(models.Produto, uuid=produto_id)
    return produto


@api.patch('/produto/{produto_id}', auth=JWTAuth(), response=schemas.ProdutoSchema)
def produto_edita(request, produto_id: str, payload: schemas.ProdutoEditaSchema):
    produto = get_object_or_404(models.Produto, uuid=produto_id)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(produto, attr, value)
    produto.save()
    return produto


@api.delete('/produto/{produto_id}', auth=JWTAuth())
def produto_exclui(request, produto_id: str):
    produto = get_object_or_404(models.Produto, uuid=produto_id)
    uuid_str = produto.uuid
    produto.delete()
    return {'successo': f'O produto {produto.nome} - {uuid_str} foi excluído.'}


@api.get('/produtos', auth=JWTAuth(), response=list[schemas.ProdutoSchema])
def produto_lista(request):
    produtos = models.Produto.objects.select_related(
        'unidade_medida'
    ).order_by('nome')
    
    return produtos


@api.post('/estoque/novo', auth=JWTAuth(), response=schemas.EstoqueSchema)
def estoque_novo(request, payload: schemas.EstoqueNovoSchema):
    armazem = models.Armazem.objects.filter(uuid=payload.armazem_id).first()
    valida_permissao_empresa(request.user, armazem.empresa)

    estoque = models.Estoque(**payload.dict())
    estoque.save()
    return estoque


@api.get('/estoque/{estoque_id}', auth=JWTAuth(), response=schemas.EstoqueSchema)
def estoque(request, estoque_id: str):
    estoque = get_object_or_404(models.Estoque, uuid=estoque_id)
    valida_permissao_empresa(request.user, estoque.armazem.empresa)
    return estoque


@api.patch('/estoque/{estoque_id}', auth=JWTAuth(), response=schemas.EstoqueSchema)
def estoque_edita(request, estoque_id: str, payload: schemas.EstoqueEditaSchema):
    estoque = get_object_or_404(models.Estoque, uuid=estoque_id)
    valida_permissao_empresa(request.user, estoque.armazem.empresa)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(estoque, attr, value)
    estoque.save()
    return estoque


@api.delete('/estoque/{estoque_id}', auth=JWTAuth())
def estoque_exclui(request, estoque_id: str):
    estoque = get_object_or_404(models.Estoque, uuid=estoque_id)
    valida_permissao_empresa(request.user, estoque.armazem.empresa)
    uuid_str = estoque.uuid
    estoque.delete()
    return {'successo': f'O item de estoque {estoque.produto.nome} - {uuid_str} foi excluído.'}


@api.get('/itens_estoque', auth=JWTAuth(), response=list[schemas.EstoqueSchema])
def estoque_lista(request, empresa_id: str | None = None):
    estoques = models.Estoque.objects.select_related(
        'armazem', 'armazem__empresa', 'produto'
    ).order_by('produto__nome')
    if empresa_id is not None:
        empresa = models.Empresa.objects.filter(uuid=empresa_id).first()
        valida_permissao_empresa(request.user, empresa)
        estoques = estoques.filter(armazem__empresa=empresa)
        return estoques

    if request.user.is_superuser:
        return estoques
    
    estoques = estoques.filter(armazem__empresa__perfil__usuario=request.user).distinct()
    return estoques
