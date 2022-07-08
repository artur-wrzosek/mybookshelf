# Generated by Django 4.0.1 on 2022-01-29 22:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finder', '0015_author_added_by_author_added_date_book_added_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='finder.profile'),
        ),
        migrations.AlterField(
            model_name='book',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='finder.profile'),
        ),
        migrations.AlterField(
            model_name='category',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='finder.profile'),
        ),
        migrations.AlterField(
            model_name='publisher',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='finder.profile'),
        ),
    ]
