# Generated by Django 4.0.3 on 2022-12-22 14:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_product_hidden_for_all'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalProperty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Название свойства')),
                ('warning_message', models.CharField(blank=True, max_length=255, null=True, verbose_name='Текст предупреждения')),
            ],
            options={
                'verbose_name': 'Дополнительное свойство товара',
                'verbose_name_plural': 'Дополнительные свойства товара',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='additional_property',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.additionalproperty', verbose_name='Дополнительное свойство'),
        ),
    ]