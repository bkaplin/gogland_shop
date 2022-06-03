# Generated by Django 4.0.3 on 2022-06-03 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_alter_user_last_name'),
        ('bot', '0004_shopsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupBotMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_text', models.TextField(default='', verbose_name='Текст сообщения')),
                ('sent', models.BooleanField(default=False, verbose_name='Отправлено')),
                ('log', models.TextField(blank=True, default='', null=True, verbose_name='Лог отправки')),
                ('users', models.ManyToManyField(related_name='group_messages', to='user.user', verbose_name='Пользователи для отправки сообщения')),
            ],
        ),
    ]
