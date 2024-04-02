import re
import uuid

from django.db import models


class ModeloBase(models.Model):
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TipoPerfil(ModeloBase):
    nome = models.CharField(max_length=50)
    sigla = models.CharField(max_length=3)

    def __str__(self):
        return f'{self.sigla} - {self.nome}'

    class Meta:
        verbose_name = 'Tipo de Perfil'
        verbose_name_plural = 'Tipos de Perfil'


class Empresa(ModeloBase):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=14)

    def __str__(self):
        cnpj_formatado = re.sub(
            r'(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})', 
            r'\1.\2.\3/\4-\5', 
            self.cnpj
        )
        return f'{self.nome} - {cnpj_formatado}'


class Perfil(ModeloBase):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    empresa = models.ForeignKey('core.Empresa', on_delete=models.PROTECT)
    tipo = models.ForeignKey('core.TipoPerfil', on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.empresa.nome} - {self.usuario.username} - {self.tipo.nome}'

    class Meta:
        verbose_name_plural = 'Perfis'


class Municipio(ModeloBase):
    UFS = (
        ('AC', 'Acre'),
        ('AL', 'Alagoas'),
        ('AM', 'Amazonas'),
        ('AP', 'Amapá'),
        ('BA', 'Bahia'),
        ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'),
        ('MA', 'Maranhão'),
        ('MG', 'Minas Gerais'),
        ('MS', 'Mato Grosso do Sul'),
        ('MT', 'Mato Grosso'),
        ('PA', 'Pará'),
        ('PB', 'Paraíba'),
        ('PE', 'Pernambuco'),
        ('PI', 'Piauí'),
        ('PR', 'Paraná'),
        ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RO', 'Rondônia'),
        ('RR', 'Roraima'),
        ('RS', 'Rio Grande do Sul'),
        ('SC', 'Santa Catarina'),
        ('SE', 'Sergipe'),
        ('SP', 'São Paulo'),
        ('TO', 'Tocantins'),
    )

    nome = models.CharField(max_length=255)
    uf = models.CharField(max_length=2, choices=UFS)

    def __str__(self):
        return f'{self.nome}/{self.uf}'


class Armazem(ModeloBase):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=50, blank=True)
    empresa = models.ForeignKey('core.Empresa', on_delete=models.PROTECT)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    complemento = models.CharField(max_length=20, blank=True)
    municipio = models.ForeignKey(
        'core.Municipio', on_delete=models.PROTECT, null=True, blank=True
    )
    cep = models.CharField(max_length=8, blank=True)

    def __str__(self):
        return f'{self.uuid} - {self.empresa.nome} - {self.nome}'
    
    class Meta:
        verbose_name_plural = 'Armazéns'


class UnidadeMedida(ModeloBase):
    nome = models.CharField(max_length=50)
    sigla = models.CharField(max_length=3)

    def __str__(self):
        return f'{self.nome} ({self.sigla})'
    
    class Meta:
        verbose_name = 'Unidade de Medida'
        verbose_name_plural = 'Unidades de Medida'


class Produto(ModeloBase):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    unidade_medida = models.ForeignKey('core.UnidadeMedida', on_delete=models.PROTECT)

    def __str__(self):
        return self.nome


class Estoque(ModeloBase):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    armazem = models.ForeignKey('core.Armazem', on_delete=models.PROTECT)
    produto = models.ForeignKey('core.Produto', on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=14, decimal_places=3)
    preco = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f'{self.uuid} - {self.armazem.nome} - {self.produto.nome}'


class Movimento(ModeloBase):
    TIPOS = (
        ('E', 'Entrada'),
        ('S', 'Saída')
    )

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    responsavel = models.ForeignKey('core.Perfil', on_delete=models.PROTECT)
    estoque = models.ForeignKey('core.Estoque', on_delete=models.PROTECT)
    tipo = models.CharField(max_length=1, choices=TIPOS)
    quantidade = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f'{self.uuid} - {self.estoque.produto.nome} - {self.get_tipo_display()}: {self.quantidade}'
