from django.contrib import admin

from controle_estoque.core import models


class ArmazemInLine(admin.StackedInline):
    model = models.Armazem
    extra = 0


@admin.register(models.Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'get_cnpj_formatado', 'criado_em', 'atualizado_em', 'ativo'
    ]
    list_filter = ['nome']
    inlines = [ArmazemInLine]

    def get_cnpj_formatado(self, obj):
        return obj.cnpj_formatado
    
    get_cnpj_formatado.short_description = 'CNPJ'


@admin.register(models.TipoPerfil)
class TipoPerfilAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sigla']


@admin.register(models.Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'empresa', 'tipo']
    list_filter = ['empresa']


@admin.register(models.Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'uf']


@admin.register(models.UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sigla']


@admin.register(models.Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'unidade_medida']


class EstoqueInLine(admin.TabularInline):
    model = models.Estoque
    extra = 0


@admin.register(models.Armazem)
class ArmazemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa']
    inlines = [EstoqueInLine]


class MovimentoInLine(admin.TabularInline):
    model = models.Movimento
    extra = 0

@admin.register(models.Estoque)
class EstoqueAdmin(admin.ModelAdmin):
    list_display = ['armazem', 'produto', 'quantidade', 'preco']
    list_filter = ['armazem', 'produto']
    inlines = [MovimentoInLine]
