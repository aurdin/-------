from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [  # noqa: RUF012
        ("catalog", "0015_alter_brand_options_rename_name_brand_brd_name_and_more"),
    ]

    operations = [  # noqa: RUF012
        migrations.RenameModel(
            old_name="Model",
            new_name="TypeModel",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="model",
            new_name="type_model",
        ),
        migrations.RenameField(
            model_name="modelcharacteristic",
            old_name="model",
            new_name="typemodel",
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "catalog_model" RENAME TO "catalog_type_model";',
            reverse_sql='ALTER TABLE "catalog_type_model" RENAME TO "catalog_model";',
        ),
    ]
