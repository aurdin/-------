from django.contrib import admin


APP_ORDER = {
    "common": 1,
    "characteristics": 2,
    "relations": 3,
}

MODEL_ORDER = {
    "common": [
        "Category",
        "Group",
        "Brand",
        "Series",
        "Type",
        "TypeModel",
        "Execution",
        "ProtectionDegree",
        "Color",
        "SupplyVariant",
    ],
    "characteristics": [
        "CharacteristicGroup",
        "Unit",
        "Characteristic",
        "TypeCharacteristic",
    ],
    "relations": [
        "GroupType",
        "SeriesType",
        "SeriesProductColor",
        "SeriesFrameColor",
        "TypeModelType",
        "TypeExecution",
    ],
}


def ordered_get_app_list(request, app_label=None):
    app_list = original_get_app_list(request, app_label)

    app_list.sort(
        key=lambda app: (
            APP_ORDER.get(app["app_label"], 100),
            app["name"].lower(),
        )
    )

    for app in app_list:
        model_order = MODEL_ORDER.get(app["app_label"], [])
        model_positions = {
            model_name: position
            for position, model_name in enumerate(model_order)
        }

        app["models"].sort(
            key=lambda model: (
                model_positions.get(model["object_name"], 100),
                model["name"].lower(),
            )
        )

    return app_list


original_get_app_list = admin.site.get_app_list
admin.site.get_app_list = ordered_get_app_list

