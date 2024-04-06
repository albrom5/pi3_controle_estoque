import re
import uuid

from ninja import ModelSchema, Schema
from ninja.errors import ValidationError
from pydantic import field_validator

from controle_estoque.core import models


class EmpresaSchema(ModelSchema):
    cnpj: str

    @field_validator('cnpj')
    @classmethod
    def cnpj_formatado(cls, v: str) -> str:
        cnpj_formatado = re.sub(
            r'(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})', 
            r'\1.\2.\3/\4-\5', 
            v
        )
        return cnpj_formatado
        
    class Meta:
        model = models.Empresa
        fields = ['uuid', 'nome']


class MunicipioSchema(ModelSchema):
    
    class Meta:
        model = models.Municipio
        fields = ['id', 'nome', 'uf']


class ArmazemSchema(ModelSchema):
    empresa: EmpresaSchema
    municipio: MunicipioSchema | None
    cep: str | None

    @field_validator('cep')
    @classmethod
    def cep_formatado(cls, v: str) -> str:
        cep_formatado = re.sub(
            r'(\d{5})(\d{3})', 
            r'\1-\2', 
            v
        )
        return cep_formatado
    
    class Meta:
        model = models.Armazem
        fields = [
            'uuid', 'nome', 'logradouro', 'numero', 'complemento', 'cep'
        ]


class ArmazemNovoSchema(ModelSchema):
    empresa_id: uuid.UUID

    class Meta:
        model = models.Armazem
        fields = [
            'nome', 'logradouro', 'numero', 'complemento', 'municipio', 'cep'
        ]


class ArmazemEditaSchema(ModelSchema):
    
    class Meta:
        model = models.Armazem
        fields = [
            'nome', 'logradouro', 'numero', 'complemento', 'municipio', 'cep'
        ]

    class Config:
        extra = 'forbid'


class UnidadeMedidaSchema(ModelSchema):

    class Meta:
        model = models.UnidadeMedida
        fields = ['id', 'nome', 'sigla']


class ProdutoSchema(ModelSchema):
    unidade_medida_sigla: str

    class Meta:
        model = models.Produto
        fields = ['uuid', 'nome']

    
class ProdutoNovoSchema(ModelSchema):
    unidade_medida_id: int

    class Meta:
        model = models.Produto
        fields = ['nome']


class ProdutoEditaSchema(Schema):
    nome: str | None = None
    unidade_medida_id: int | None = None
    
    class Config:
        extra = 'forbid'


class EstoqueSchema(ModelSchema):
    armazem_uuid: uuid.UUID
    armazem_nome: str
    produto_uuid: uuid.UUID
    produto_nome: str

    class Meta:
        model = models.Estoque
        fields = ['uuid', 'quantidade', 'preco']


class EstoqueNovoSchema(ModelSchema):
    armazem_id: uuid.UUID
    produto_id: uuid.UUID

    class Meta:
        model = models.Estoque
        fields = ['quantidade', 'preco']


class EstoqueEditaSchema(ModelSchema):
    
    class Meta:
        model = models.Estoque
        fields = ['preco']


class ListaSchema(Schema):
    quantidade: int
    lista: list


class PerfilSchema(Schema):
    usuario: str
    nome: str
    empresa_uuid: uuid.UUID
    empresa_nome: str
    empresa_cnpj: str
    tipo: str


class MovimentoNovoSchema(ModelSchema):
    estoque_id: uuid.UUID
    tipo: str 

    @field_validator('tipo', mode='before')
    @classmethod
    def valida_tipo(cls, v: str) -> str:
        if v not in [models.Movimento.ENTRADA, models.Movimento.SAIDA]:
            raise ValidationError('Tipo não permitido, escolha E (Entrada) ou S (Saída)')
        return v

    class Meta:
        model = models.Movimento
        fields = ['quantidade']
