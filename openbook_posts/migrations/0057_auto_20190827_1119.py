# Generated by Django 2.2.4 on 2019-08-27 09:19

from django.db import migrations, models
import imagekit.models.fields
import openbook_posts.helpers


class Migration(migrations.Migration):

    dependencies = [
        ('openbook_posts', '0056_auto_20190826_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='media_thumbnail',
            field=imagekit.models.fields.ProcessedImageField(null=True, upload_to=openbook_posts.helpers.upload_to_post_image_directory, verbose_name='thumbnail'),
        ),
        migrations.AlterField(
            model_name='post',
            name='media_width',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='media width'),
        ),
    ]
