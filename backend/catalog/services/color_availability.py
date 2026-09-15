from __future__ import annotations


class ColorAvailabilityService:
    @staticmethod
    def is_allowed(
        product_type: Type,
        series: Series | None,
        color: Color,
    ) -> bool:
        """
        Проверяет, допустим ли цвет для комбинации Type + Series.

        Правила:
        - неактивный Color запрещён;
        - если для Type нет активных ограничений — ограничений Type нет;
        - если для Series нет активных ограничений — ограничений Series нет;
        - если ограничения заданы, цвет должен входить в них;
        - при наличии обоих ограничений действует пересечение.
        """

        if not color.status:
            return False

        type_colors = ColorAvailabilityService._get_type_colors(product_type)

        if type_colors is not None and color.id not in type_colors:
            return False

        if series is not None:
            series_colors = ColorAvailabilityService._get_series_colors(series)

            if series_colors is not None and color.id not in series_colors:
                return False

        return True

    @staticmethod
    def _get_type_colors(product_type: Type) -> set[int] | None:
        """
        Возвращает множество разрешённых цветов для Type.

        None означает, что для Type ограничений нет.
        """
        queryset = product_type.type_colors.filter(
            status=True,
            color__status=True,
        ).values_list("color_id", flat=True)

        color_ids = set(queryset)

        return color_ids if color_ids else None

    @staticmethod
    def _get_series_colors(series: Series) -> set[int] | None:
        """
        Возвращает множество разрешённых цветов для Series.

        None означает, что для Series ограничений нет.
        """
        queryset = series.series_colors.filter(
            status=True,
            color__status=True,
        ).values_list("color_id", flat=True)

        color_ids = set(queryset)

        return color_ids if color_ids else None
