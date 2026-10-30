# Product schema introduced after the historical catalog 0001 marker.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0001_initial'),
        ('characteristics', '0013_characteristicvalue_cv_description_and_more'),
        ('common', '0030_protectiondegree_ptd_name_en_and_more'),
    ]
    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prd_code', models.CharField(editable=False, max_length=20, unique=True)),
                ('prd_article', models.CharField(max_length=255, unique=True)),
                ('prd_name', models.CharField(blank=True, max_length=1024)),
                ('prd_name_en', models.CharField(blank=True, max_length=1024, null=True)),
                ('prd_name_ru', models.CharField(blank=True, max_length=1024, null=True)),
                ('prd_name_uk', models.CharField(blank=True, max_length=1024, null=True)),
                ('prd_description', models.TextField(blank=True)),
                ('prd_description_en', models.TextField(blank=True, null=True)),
                ('prd_description_ru', models.TextField(blank=True, null=True)),
                ('prd_description_uk', models.TextField(blank=True, null=True)),
                ('prd_notes', models.TextField(blank=True)),
                ('prd_notes_en', models.TextField(blank=True, null=True)),
                ('prd_notes_ru', models.TextField(blank=True, null=True)),
                ('prd_notes_uk', models.TextField(blank=True, null=True)),
                ('status', models.BooleanField(default=True)),
                ('product_image_1', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('product_image_2', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('product_image_3', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('packaging', models.TextField(blank=True, null=True)),
                ('sales_unit', models.CharField(blank=True, max_length=50)),
                ('barcode', models.CharField(blank=True, max_length=255, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.category')),
                ('color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.color')),
                ('execution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.execution')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.group')),
                ('protection_degree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.protectiondegree')),
                ('series', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.series')),
                ('supply_variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.supplyvariant')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.type')),
                ('type_model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='common.typemodel')),
            ],
            options={
                'db_table': 'catalog_product',
                'ordering': ('prd_article',),
            },
        ),
        migrations.CreateModel(
            name='ProductNameRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='product_name_rule', to='common.type')),
            ],
            options={
                'verbose_name': 'Product name rule',
                'verbose_name_plural': 'Product name rules',
                'db_table': 'catalog_product_name_rule',
            },
        ),
        migrations.CreateModel(
            name='ProductCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_type', models.CharField(choices=[('text', 'Text'), ('number', 'Number'), ('boolean', 'Boolean'), ('reference', 'Reference')], default='text', max_length=20)),
                ('value_text', models.TextField(blank=True, null=True)),
                ('value_number', models.DecimalField(blank=True, decimal_places=6, max_digits=20, null=True)),
                ('value_boolean', models.BooleanField(blank=True, null=True)),
                ('status', models.BooleanField(default=True)),
                ('characteristic', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product_characteristics', to='characteristics.characteristic')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characteristics', to='catalog.product')),
                ('value_reference', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='product_characteristics', to='characteristics.characteristicvalue')),
            ],
            options={
                'db_table': 'catalog_product_characteristic',
                'constraints': [models.UniqueConstraint(fields=('product', 'characteristic'), name='uq_product_characteristic')],
            },
        ),
        migrations.CreateModel(
            name='ProductNameRuleComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('component', models.CharField(choices=[('type', 'Type'), ('model', 'Model'), ('execution', 'Execution'), ('protection_degree', 'Protection degree'), ('characteristics', 'Characteristics'), ('color', 'Color'), ('supply_variant', 'Supply variant')], max_length=32)),
                ('position', models.PositiveSmallIntegerField()),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='catalog.productnamerule')),
            ],
            options={
                'db_table': 'catalog_product_name_rule_component',
                'ordering': ('position',),
                'constraints': [models.UniqueConstraint(fields=('rule', 'component'), name='uq_name_rule_component'), models.UniqueConstraint(fields=('rule', 'position'), name='uq_name_rule_position')],
            },
        ),
    ]
