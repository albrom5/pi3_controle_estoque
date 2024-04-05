import re
import uuid

from django.db import models
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce


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

    @property
    def cnpj_formatado(self):
        cnpj_formatado = re.sub(
            r'(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})', 
            r'\1.\2.\3/\4-\5', 
            self.cnpj
        )
        return cnpj_formatado

    def __str__(self):
        return f'{self.nome} - {self.cnpj_formatado}'


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
    
    def save(self, *args, **kwargs):
        novo_objeto = self.criado_em is None
        super().save(*args, **kwargs)
        if novo_objeto:
            self.gera_movimento_inicial()

    def gera_movimento_inicial(self):
        movimento = Movimento(
            estoque=self,
            tipo=Movimento.ENTRADA,
            quantidade=self.quantidade
        )
        movimento.save()


class Movimento(ModeloBase):
    ENTRADA = 'E'
    SAIDA = 'S'
    TIPOS = (
        (ENTRADA, 'Entrada'),
        (SAIDA, 'Saída')
    )

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    responsavel = models.ForeignKey('core.Perfil', on_delete=models.PROTECT, null=True)
    estoque = models.ForeignKey('core.Estoque', on_delete=models.PROTECT, related_name='movimentos')
    tipo = models.CharField(max_length=1, choices=TIPOS)
    quantidade = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f'{self.uuid} - {self.estoque.produto.nome} - {self.get_tipo_display()}: {self.quantidade}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.atualiza_estoque()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.atualiza_estoque()

    def atualiza_estoque(self):
        quantidade_total = Movimento.objects.filter(
            estoque=self.estoque
        ).aggregate(
            total_entrada=Coalesce(
                Sum('quantidade', filter=Q(tipo=Movimento.ENTRADA)), Value(0), output_field=models.DecimalField()
            ),
            total_saida=Coalesce(
                Sum('quantidade', filter=Q(tipo=Movimento.SAIDA)), Value(0), output_field=models.DecimalField()
            ),
            quantidade_total=F('total_entrada') - F('total_saida')
        )['quantidade_total']
        self.estoque.quantidade = quantidade_total
        self.estoque.save()
