# Generated by Django 4.0.3 on 2022-03-31 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания'),
        ),
        migrations.AddField(
            model_name='order',
            name='in_cart',
            field=models.BooleanField(default=True, verbose_name='В корзине'),
        ),
    ]
