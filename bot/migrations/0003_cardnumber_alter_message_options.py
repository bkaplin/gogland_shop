# Generated by Django 4.0.3 on 2022-05-26 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_alter_chat_options_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=255, verbose_name='Номер карты')),
                ('owner', models.CharField(max_length=255, verbose_name='Владелец')),
                ('is_active', models.BooleanField(default=False, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Номер карты (админ)',
                'verbose_name_plural': 'Номера карт (админ)',
            },
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'verbose_name': 'Сообщение', 'verbose_name_plural': 'Сообщения'},
        ),
    ]
