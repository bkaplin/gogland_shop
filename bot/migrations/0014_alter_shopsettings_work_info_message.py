# Generated by Django 4.0.3 on 2023-05-14 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0013_remove_shopsettings_work_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopsettings',
            name='work_info_message',
            field=models.TextField(default='Время работы магазина {}', help_text='Сообщение с информацией о графике работы, отображается в самом верху сообщения от бота пользователю. Оставить скобки "{}" для вставки времени работы в нужное место сообщения', verbose_name='Сообщение о графике работы магазина'),
        ),
    ]
