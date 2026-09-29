import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def convert_cart_statuses(apps, schema_editor):
    Cart = apps.get_model("cart", "Cart")

    Cart.objects.filter(status="true").update(status="busy")
    Cart.objects.filter(status="false").update(status="free")


class Migration(migrations.Migration):
    atomic = False
    
    dependencies = [  # noqa: RUF012
        ("cart", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [  # noqa: RUF012
        migrations.RemoveConstraint(
            model_name="cart",
            name="ck_cart_owner",
        ),
        migrations.AlterField(
            model_name="cart",
            name="customer",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cart",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="cart",
            name="status",
            field=models.CharField(
                choices=[
                    ("free", "Free"),
                    ("busy", "Busy"),
                ],
                default="busy",
                max_length=10,
            ),
        ),
        migrations.RunPython(
            convert_cart_statuses,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        status="free",
                        customer__isnull=True,
                        session_key__isnull=True,
                    )
                    | models.Q(
                        status="busy",
                        customer__isnull=True,
                        session_key__isnull=False,
                    )
                    | models.Q(
                        status="busy",
                        customer__isnull=False,
                        session_key__isnull=True,
                    )
                ),
                name="ck_cart_state",
            ),
        ),
    ]
