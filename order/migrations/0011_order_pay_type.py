# Generated by Django 4.0.3 on 2022-09-03 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0010_orderitem_item_sum_alter_order_shipped'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='pay_type',
            field=models.CharField(choices=[('CASH', 'Наличка'), ('CARD', 'Карта')], max_length=50, null=True, verbose_name='Тип оплаты'),
        ),
    ]
