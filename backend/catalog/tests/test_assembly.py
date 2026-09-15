from django.core.exceptions import ValidationError
from django.test import TestCase
from decimal import Decimal

from catalog.models import (
    AssemblyComponent,
    Brand,
    Category,
    Group,
    Product,
    Type,
)
from catalog.services.assembly import add_component


class AssemblyDependencyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Test Category")
        cls.group = Group.objects.create(name="Test Group")
        cls.brand = Brand.objects.create(name="Test Brand")
        cls.type = Type.objects.create(name="Test Type")

    def create_product(self, article):
        return Product.objects.create(
            article=article,
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="pcs",
        )

    def test_cyc_01_regular_component_is_allowed(self):
        assembly = self.create_product("A")
        component = self.create_product("P")

        relation = add_component(
            assembly,
            component,
            1,
        )

        self.assertIsNotNone(relation.pk)
        self.assertTrue(
            AssemblyComponent.objects.filter(
                assembly_product=assembly,
                component_product=component,
            ).exists()
        )

    def test_cyc_02_nested_assembly_is_allowed(self):
        assembly_a = self.create_product("A")
        assembly_b = self.create_product("B")

        add_component(assembly_a, assembly_b, 1)

        self.assertTrue(
            AssemblyComponent.objects.filter(
                assembly_product=assembly_a,
                component_product=assembly_b,
            ).exists()
        )

    def test_cyc_03_self_reference_is_rejected(self):
        assembly = self.create_product("A")

        with self.assertRaises(ValidationError):
            add_component(
                assembly,
                assembly,
                1,
            )

        self.assertFalse(
            AssemblyComponent.objects.filter(
                assembly_product=assembly,
                component_product=assembly,
            ).exists()
        )

    def test_cyc_04_direct_cycle_is_rejected(self):
        assembly_a = self.create_product("A")
        assembly_b = self.create_product("B")

        add_component(assembly_a, assembly_b, 1)

        with self.assertRaises(ValidationError):
            add_component(
                assembly_b,
                assembly_a,
                1,
            )

        self.assertFalse(
            AssemblyComponent.objects.filter(
                assembly_product=assembly_b,
                component_product=assembly_a,
            ).exists()
        )

    def test_cyc_05_cycle_of_three_is_rejected(self):
        assembly_a = self.create_product("A")
        assembly_b = self.create_product("B")
        assembly_c = self.create_product("C")

        add_component(assembly_a, assembly_b, 1)
        add_component(assembly_b, assembly_c, 1)

        with self.assertRaises(ValidationError):
            add_component(
                assembly_c,
                assembly_a,
                1,
            )

        self.assertFalse(
            AssemblyComponent.objects.filter(
                assembly_product=assembly_c,
                component_product=assembly_a,
            ).exists()
        )

    def test_cyc_06_long_cycle_is_rejected(self):
        assembly_a = self.create_product("A")
        assembly_b = self.create_product("B")
        assembly_c = self.create_product("C")
        assembly_d = self.create_product("D")

        add_component(assembly_a, assembly_b, 1)
        add_component(assembly_b, assembly_c, 1)
        add_component(assembly_c, assembly_d, 1)

        with self.assertRaises(ValidationError):
            add_component(
                assembly_d,
                assembly_a,
                1,
            )

        self.assertFalse(
            AssemblyComponent.objects.filter(
                assembly_product=assembly_d,
                component_product=assembly_a,
            ).exists()
        )

    def test_cyc_07_existing_chain_cycle_is_rejected(self):
        assembly_a = self.create_product("A")
        assembly_b = self.create_product("B")
        assembly_c = self.create_product("C")
        assembly_d = self.create_product("D")

        add_component(assembly_b, assembly_c, 1)
        add_component(assembly_c, assembly_d, 1)
        add_component(assembly_d, assembly_a, 1)

        with self.assertRaises(ValidationError):
            add_component(
                assembly_a,
                assembly_b,
                1,
            )

        self.assertFalse(
            AssemblyComponent.objects.filter(
                assembly_product=assembly_a,
                component_product=assembly_b,
            ).exists()
        )

    def test_cyc_08_independent_chains_are_allowed(self):
        assembly_a = self.create_product("A")
        assembly_b = self.create_product("B")
        assembly_c = self.create_product("C")
        assembly_d = self.create_product("D")

        add_component(assembly_a, assembly_b, 1)
        add_component(assembly_c, assembly_d, 1)

        self.assertEqual(
            AssemblyComponent.objects.count(),
            2,
        )

    def test_cyc_09_multiple_components_are_allowed(self):
        assembly = self.create_product("A")
        component_b = self.create_product("B")
        component_c = self.create_product("C")
        component_d = self.create_product("D")

        add_component(assembly, component_b, 1)
        add_component(assembly, component_c, 2)
        add_component(assembly, component_d, 3)

        self.assertEqual(
            AssemblyComponent.objects.filter(
                assembly_product=assembly,
            ).count(),
            3,
        )

    def test_positive_integer_quantity_allowed(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        component = add_component(
            assembly,
            component,
            Decimal("1"),
        )

        self.assertEqual(component.quantity, Decimal("1"))

    def test_positive_fractional_quantity_allowed(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        component = add_component(
            assembly,
            component,
            Decimal("1.125"),
        )

        self.assertEqual(component.quantity, Decimal("1.125"))

    def test_zero_quantity_rejected(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        with self.assertRaises(ValidationError):
            add_component(
                assembly,
                component,
                Decimal("0"),
            )

    def test_more_than_three_decimal_places_rejected(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        with self.assertRaises(ValidationError):
            add_component(
                assembly,
                component,
                Decimal("1.1255"),
            )

    def test_duplicate_component_in_same_assembly_rejected(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        add_component(
            assembly,
            component,
            Decimal("1"),
        )

        with self.assertRaises(ValidationError):
            add_component(
                assembly,
                component,
                Decimal("2"),
            )    

    def test_same_component_allowed_in_different_assemblies(self):
        assembly_a = self.create_product("Assembly A")
        assembly_b = self.create_product("Assembly B")
        component = self.create_product("Component")

        component_a = add_component(
            assembly_a,
            component,
            Decimal("1"),
        )

        component_b = add_component(
            assembly_b,
            component,
            Decimal("2"),
        )

        self.assertEqual(component_a.component_product, component)
        self.assertEqual(component_b.component_product, component)

        self.assertEqual(
            AssemblyComponent.objects.filter(
                component_product=component,
            ).count(),
            2,
        )

    def test_maximum_quantity_allowed(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        component = add_component(
            assembly,
            component,
            Decimal("999999999.999"),
        )

        self.assertEqual(
            component.quantity,
            Decimal("999999999.999"),
        )

    def test_quantity_exceeding_max_digits_rejected(self):
        assembly = self.create_product("Assembly")
        component = self.create_product("Component")

        with self.assertRaises(ValidationError):
            add_component(
                assembly,
                component,
                Decimal("1000000000.000"),
            )

    def test_nonexistent_component_product_rejected(self):
        assembly = self.create_product("Assembly")
        nonexistent_component = Product(id=999999)

        with self.assertRaises(ValidationError):
            add_component(
                assembly,
                nonexistent_component,
                Decimal("1"),
            )                        