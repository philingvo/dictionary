# Generated by Django 3.1.7 on 2021-04-29 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pronunciation', '0005_pronunciation_file_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='pronunciation_file',
            name='choosen',
            field=models.IntegerField(default=False),
        ),
    ]