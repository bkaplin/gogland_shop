# Generated by Django 4.0.3 on 2022-07-20 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0007_order_comment_alter_orderitem_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='in_process',
            field=models.BooleanField(default=False, verbose_name='В процессе изменения кол-ва'),
        ),
    ]
