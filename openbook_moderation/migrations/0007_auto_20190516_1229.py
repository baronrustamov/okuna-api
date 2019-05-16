# Generated by Django 2.2 on 2019-05-16 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openbook_moderation', '0006_auto_20190514_1348'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='moderatedobject',
            name='submitted',
        ),
        migrations.AddField(
            model_name='moderatedobject',
            name='object_audit_snapshot',
            field=models.TextField(default='', verbose_name='object_audit_snapshot'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='moderationpenalty',
            name='type',
            field=models.CharField(choices=[('S', 'Suspension')], default='S', max_length=5),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='moderatedobject',
            name='approved',
            field=models.BooleanField(null=True, verbose_name='approved'),
        ),
        migrations.AlterField(
            model_name='moderationpenalty',
            name='duration',
            field=models.DurationField(null=True),
        ),
    ]
