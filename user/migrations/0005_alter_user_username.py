# Generated by Django 4.0.3 on 2022-05-28 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='username'),
        ),
    ]
