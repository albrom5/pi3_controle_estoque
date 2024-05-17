from datetime import datetime

from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from controle_estoque.core import models, schemas
from controle_estoque.core.utils import valida_permissao_empresa

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)


@api.get('/unidades_de_medida', auth=JWTAuth(), response=schemas.ListaSchema)
def unidade_medida_lista(request):
    unidades = models.UnidadeMedida.objects.order_by('nome')
    
    lista_unidades = [schemas.UnidadeMedidaSchema(**u) for u in unidades.values()] 
    response = schemas.ListaSchema(quantidade=unidades.count(), lista=lista_unidades)
    return response


@api.get('/marcas', auth=JWTAuth(), response=schemas.ListaSchema)
def marca_lista(request):
    marcas = models.Marca.objects.order_by('nome')
    
    lista_marcas = [schemas.MarcaSchema(**m) for m in marcas.values()] 
    response = schemas.ListaSchema(quantidade=marcas.count(), lista=lista_marcas)
    return response


@api.post('/marca/nova', auth=JWTAuth(), response=schemas.MarcaSchema)
def marca_nova(request, payload: schemas.MarcaNovaSchema):
    marca = models.Marca(**payload.dict())
    try:
        marca.save()
    except IntegrityError:
        raise HttpError(400, 'Já existe uma marca cadastrada com o mesmo nome.')
    return marca


@api.get('/municipios', auth=JWTAuth(), response=schemas.ListaSchema)
def municipios_lista(request):
    municipios = models.Municipio.objects.order_by('uf', 'nome')
    lista_municipios = [schemas.MunicipioSchema(**m) for m in municipios.values()] 
    response = schemas.ListaSchema(quantidade=municipios.count(), lista=lista_municipios)
    return response


@api.post('/armazem/novo', auth=JWTAuth(), response=schemas.ArmazemSchema)
def armazem_novo(request, payload: schemas.ArmazemNovoSchema):
    empresa = models.Empresa.objects.filter(uuid=payload.empresa_id).first()
    valida_permissao_empresa(request.user, empresa)

    armazem = models.Armazem(**payload.dict())
    armazem.save()
    response = schemas.ArmazemSchema(
        uuid=armazem.uuid,
        nome=armazem.nome,
        logradouro=armazem.logradouro,
        numero=armazem.numero,
        complemento=armazem.complemento,
        cep=armazem.cep,
        empresa=armazem.empresa.nome,
        municipio=f'{armazem.municipio.nome}/{armazem.municipio.uf}' if armazem.municipio is not None else ''
    )
    return response


@api.get('/armazem/{armazem_id}', auth=JWTAuth(), response=schemas.ArmazemSchema)
def armazem(request, armazem_id: str):
    armazem = get_object_or_404(models.Armazem, uuid=armazem_id)
    valida_permissao_empresa(request.user, armazem.empresa)
    response = schemas.ArmazemSchema(
        uuid=armazem.uuid,
        nome=armazem.nome,
        logradouro=armazem.logradouro,
        numero=armazem.numero,
        complemento=armazem.complemento,
        cep=armazem.cep,
        empresa=armazem.empresa.nome,
        municipio=f'{armazem.municipio.nome}/{armazem.municipio.uf}' if armazem.municipio is not None else ''
    )
    return response


@api.patch('/armazem/{armazem_id}', auth=JWTAuth(), response=schemas.ArmazemSchema)
def armazem_edita(request, armazem_id: str, payload: schemas.ArmazemEditaSchema):
    armazem = get_object_or_404(models.Armazem, uuid=armazem_id)
    valida_permissao_empresa(request.user, armazem.empresa)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(armazem, attr, value)
    armazem.save()
    response = schemas.ArmazemSchema(
        uuid=armazem.uuid,
        nome=armazem.nome,
        logradouro=armazem.logradouro,
        numero=armazem.numero,
        complemento=armazem.complemento,
        cep=armazem.cep,
        empresa=armazem.empresa.nome,
        municipio=f'{armazem.municipio.nome}/{armazem.municipio.uf}' if armazem.municipio is not None else ''
    )
    return response


@api.delete('/armazem/{armazem_id}', auth=JWTAuth())
def armazem_exclui(request, armazem_id: str):
    armazem = get_object_or_404(models.Armazem, uuid=armazem_id)
    valida_permissao_empresa(request.user, armazem.empresa)
    uuid_str = armazem.uuid
    armazem.delete()
    return {'successo': f'O armazém {armazem.nome} - {uuid_str} foi excluído.'}


@api.get('/armazens', auth=JWTAuth(), response=schemas.ListaSchema)
def armazem_lista(request, empresa_id: str | None = None):
    armazens = models.Armazem.objects.select_related(
        'empresa', 'municipio'
    ).order_by('nome')
    if empresa_id is not None:
        empresa = models.Empresa.objects.filter(uuid=empresa_id).first()
        valida_permissao_empresa(request.user, empresa)
        armazens = armazens.filter(empresa=empresa)

    elif not request.user.is_superuser:
        armazens = armazens.filter(empresa__perfil__usuario=request.user).distinct()
    
    lista_armazens = [
        schemas.ArmazemSchema(
            uuid=a.uuid,
            empresa=a.empresa.nome, 
            nome=a.nome,
            logradouro=a.logradouro,
            numero=a.numero,
            complemento=a.complemento,
            cep=a.cep,
            municipio=f'{a.municipio.nome}/{a.municipio.uf}' if a.municipio is not None else ''
        ) 
        for a in armazens
    ]
    response = schemas.ListaSchema(quantidade=armazens.count(), lista=lista_armazens)
    return response


@api.post('/produto/novo', auth=JWTAuth(), response=schemas.ProdutoSchema)
def produto_novo(request, payload: schemas.ProdutoNovoSchema):
    produto = models.Produto(**payload.dict())
    try:
        produto.save()
    except IntegrityError:
        raise HttpError(400, 'Já existe um produto cadastrado com o mesmo nome, unidade de medida e marca.')
    
    response = schemas.ProdutoSchema(
        uuid=produto.uuid,
        nome=produto.nome,
        unidade_medida_sigla=produto.unidade_medida.sigla,
        unidade_medida_id=produto.unidade_medida.id, 
        marca=produto.marca.nome if produto.marca is not None else '',
        marca_id=produto.marca.uuid if produto.marca is not None else None
    )
    return response


@api.get('/produto/{produto_id}', auth=JWTAuth(), response=schemas.ProdutoSchema)
def produto(request, produto_id: str):
    produto = get_object_or_404(models.Produto, uuid=produto_id)
    response = schemas.ProdutoSchema(
        uuid=produto.uuid,
        nome=produto.nome,
        unidade_medida_sigla=produto.unidade_medida.sigla,
        unidade_medida_id=produto.unidade_medida.id, 
        marca=produto.marca.nome if produto.marca is not None else '',
        marca_id=produto.marca.uuid if produto.marca is not None else None
    )
    return response


@api.patch('/produto/{produto_id}', auth=JWTAuth(), response=schemas.ProdutoSchema)
def produto_edita(request, produto_id: str, payload: schemas.ProdutoEditaSchema):
    produto = get_object_or_404(models.Produto, uuid=produto_id)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(produto, attr, value)
    produto.save()
    response = schemas.ProdutoSchema(
        uuid=produto.uuid,
        nome=produto.nome,
        unidade_medida_sigla=produto.unidade_medida.sigla,
        unidade_medida_id=produto.unidade_medida.id, 
        marca=produto.marca.nome if produto.marca is not None else '',
        marca_id=produto.marca.uuid if produto.marca is not None else None
    )
    return response


@api.delete('/produto/{produto_id}', auth=JWTAuth())
def produto_exclui(request, produto_id: str):
    produto = get_object_or_404(models.Produto, uuid=produto_id)
    uuid_str = produto.uuid
    produto.delete()
    return {'successo': f'O produto {produto.nome} - {uuid_str} foi excluído.'}


@api.get('/produtos', auth=JWTAuth(), response=schemas.ListaSchema)
def produto_lista(request):
    produtos = models.Produto.objects.select_related(
        'unidade_medida'
    ).order_by('nome')
    
    lista_produtos = [
        schemas.ProdutoSchema(
            uuid=p.uuid,
            nome=p.nome,
            unidade_medida_sigla=p.unidade_medida.sigla, 
            unidade_medida_id=p.unidade_medida.id, 
            marca=p.marca.nome if p.marca is not None else '',
            marca_id=p.marca.uuid if p.marca is not None else None
        ) 
        for p in produtos
    ] 
    response = schemas.ListaSchema(quantidade=produtos.count(), lista=lista_produtos)
    return response
    

@api.post('/estoque/novo', auth=JWTAuth(), response=schemas.EstoqueSchema)
def estoque_novo(request, payload: schemas.EstoqueNovoSchema):
    armazem = models.Armazem.objects.filter(uuid=payload.armazem_id).first()
    valida_permissao_empresa(request.user, armazem.empresa)

    estoque = models.Estoque(**payload.dict())
    estoque.save()
    response = schemas.EstoqueSchema(
        uuid=estoque.uuid,
        armazem_uuid=estoque.armazem.uuid,
        armazem_nome=estoque.armazem.nome,
        produto_uuid=estoque.produto.uuid,
        produto_nome=estoque.produto.nome,
        produto_unidade_medida=estoque.produto.unidade_medida.sigla,
        produto_marca=estoque.produto.marca.nome if estoque.produto.marca is not None else '',
        quantidade=estoque.quantidade,
        preco=estoque.preco
    )
    return response


@api.get('/estoque/{estoque_id}', auth=JWTAuth(), response=schemas.EstoqueSchema)
def estoque(request, estoque_id: str):
    estoque = get_object_or_404(models.Estoque, uuid=estoque_id)
    valida_permissao_empresa(request.user, estoque.armazem.empresa)
    response = schemas.EstoqueSchema(
        uuid=estoque.uuid,
        armazem_uuid=estoque.armazem.uuid,
        armazem_nome=estoque.armazem.nome,
        produto_uuid=estoque.produto.uuid,
        produto_nome=estoque.produto.nome,
        produto_unidade_medida=estoque.produto.unidade_medida.sigla,
        produto_marca=estoque.produto.marca.nome if estoque.produto.marca is not None else '',
        quantidade=estoque.quantidade,
        preco=estoque.preco
    )
    return response


@api.patch('/estoque/{estoque_id}', auth=JWTAuth(), response=schemas.EstoqueSchema)
def estoque_edita(request, estoque_id: str, payload: schemas.EstoqueEditaSchema):
    estoque = get_object_or_404(models.Estoque, uuid=estoque_id)
    valida_permissao_empresa(request.user, estoque.armazem.empresa)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(estoque, attr, value)
    estoque.save()
    response = schemas.EstoqueSchema(
        uuid=estoque.uuid,
        armazem_uuid=estoque.armazem.uuid,
        armazem_nome=estoque.armazem.nome,
        produto_uuid=estoque.produto.uuid,
        produto_nome=estoque.produto.nome,
        produto_unidade_medida=estoque.produto.unidade_medida.sigla,
        produto_marca=estoque.produto.marca.nome if estoque.produto.marca is not None else '',
        quantidade=estoque.quantidade,
        preco=estoque.preco
    )
    return response


@api.delete('/estoque/{estoque_id}', auth=JWTAuth())
def estoque_exclui(request, estoque_id: str):
    estoque = get_object_or_404(models.Estoque, uuid=estoque_id)
    valida_permissao_empresa(request.user, estoque.armazem.empresa)
    uuid_str = estoque.uuid
    try:
        estoque.delete()
    except ProtectedError:
        raise HttpError(400, 'Não é possível excluir o item pois há movimentação registrada.')
    return {'successo': f'O item de estoque {estoque.produto.nome} - {uuid_str} foi excluído.'}


@api.get('/itens_estoque', auth=JWTAuth(), response=schemas.ListaSchema)
def estoque_lista(request, empresa_id: str | None = None):
    estoques = models.Estoque.objects.select_related(
        'armazem', 'armazem__empresa', 'produto', 
        'produto__unidade_medida', 'produto__marca'
    ).order_by('produto__nome')
    if empresa_id is not None:
        empresa = models.Empresa.objects.filter(uuid=empresa_id).first()
        valida_permissao_empresa(request.user, empresa)
        estoques = estoques.filter(armazem__empresa=empresa)

    elif not request.user.is_superuser:
        estoques = estoques.filter(
            armazem__empresa__perfil__usuario=request.user
        ).distinct()
    
    lista_estoques = [
        schemas.EstoqueSchema(
            uuid=e.uuid,
            armazem_uuid=e.armazem.uuid,
            armazem_nome=e.armazem.nome,
            produto_uuid=e.produto.uuid,
            produto_nome=e.produto.nome,
            produto_unidade_medida=e.produto.unidade_medida.sigla,
            produto_marca=e.produto.marca.nome if e.produto.marca is not None else '',
            quantidade=e.quantidade,
            preco=e.preco
        ) 
        for e in estoques
    ] 
    
    response = schemas.ListaSchema(quantidade=estoques.count(), lista=lista_estoques)
    return response


@api.get('/empresas', auth=JWTAuth(), response=schemas.ListaSchema)
def empresa_lista(request):
    empresas = models.Empresa.objects.order_by('nome')
    
    if not request.user.is_superuser:
        empresas = empresas.filter(perfil__usuario=request.user).distinct()
    
    lista_empresas = [schemas.EmpresaSchema(**e) for e in empresas.values()]
    response = schemas.ListaSchema(quantidade=empresas.count(), lista=lista_empresas)
    return response


@api.get('/perfis', auth=JWTAuth(), response=schemas.ListaSchema)
def perfil_lista(request, empresa_id: str | None = None):
    perfis = models.Perfil.objects.select_related(
        'tipo'
    ).order_by('empresa__nome', 'usuario__username')
    if empresa_id is not None:
        empresa = models.Empresa.objects.filter(uuid=empresa_id).first()
        valida_permissao_empresa(request.user, empresa)
        perfis = perfis.filter(empresa=empresa)

    elif not request.user.is_superuser:
        perfis = perfis.filter(empresa__perfil__usuario=request.user).distinct()
    
    lista_perfis = [
        schemas.PerfilSchema(
            usuario=p.usuario.username,
            nome=p.usuario.first_name,
            empresa_uuid=p.empresa.uuid,
            empresa_nome=p.empresa.nome,            
            empresa_cnpj=p.empresa.cnpj,                        
            tipo=p.tipo.nome
        ) 
        for p in perfis
    ]
    response = schemas.ListaSchema(quantidade=perfis.count(), lista=lista_perfis)
    return response


@api.post('/movimento/novo', auth=JWTAuth(), response=schemas.EstoqueSchema)
def movimento_novo(request, payload: schemas.MovimentoNovoSchema):
    estoque = models.Estoque.objects.filter(uuid=payload.estoque_id).first()
    valida_permissao_empresa(request.user, estoque.armazem.empresa)

    movimento = models.Movimento(**payload.dict())
    movimento.responsavel = request.user.perfil_set.filter(
        empresa=estoque.armazem.empresa
    ).first()
    movimento.criado_em = datetime.now()
    movimento.save()
    response = schemas.EstoqueSchema(
        uuid=estoque.uuid,
        armazem_uuid=movimento.estoque.armazem.uuid,
        armazem_nome=movimento.estoque.armazem.nome,
        produto_uuid=movimento.estoque.produto.uuid,
        produto_nome=movimento.estoque.produto.nome,
        produto_unidade_medida=estoque.produto.unidade_medida.sigla,
        produto_marca=estoque.produto.marca.nome if estoque.produto.marca is not None else '',
        quantidade=movimento.estoque.quantidade,
        preco=movimento.estoque.preco
    )
    return response
