<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { useCatalogStore } from '../stores/catalog'

const route = useRoute()
const catalogStore = useCatalogStore()
const cartStore = useCartStore()

const productId = Number(route.params.id)

const addToCart = async () => {
    await cartStore.addItem({
        product_id: productId,
        quantity: 1,
    })
}

onMounted(async () => {
    await catalogStore.fetchProduct(productId)
})
</script>

<template>
    <main>
        <p>
            <RouterLink to="/catalog">
                ← Вернуться в каталог
            </RouterLink>
        </p>

        <p v-if="catalogStore.loadingProduct">
            Загрузка товара...
        </p>

        <template v-else-if="catalogStore.selectedProduct">
            <h1>
                {{ catalogStore.selectedProduct.name }}
            </h1>

            <p>
                Артикул:
                {{ catalogStore.selectedProduct.article }}
            </p>

            <section>
                <h2>Основные данные</h2>

                <p v-if="catalogStore.selectedProduct.category">
                    Категория:
                    {{ catalogStore.selectedProduct.category.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.group">
                    Группа:
                    {{ catalogStore.selectedProduct.group.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.brand">
                    Бренд:
                    {{ catalogStore.selectedProduct.brand.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.series">
                    Серия:
                    {{ catalogStore.selectedProduct.series.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.type">
                    Тип:
                    {{ catalogStore.selectedProduct.type.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.model">
                    Модель:
                    {{ catalogStore.selectedProduct.model.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.execution">
                    Исполнение:
                    {{ catalogStore.selectedProduct.execution.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.color">
                    Цвет:
                    {{ catalogStore.selectedProduct.color.name }}
                </p>

                <p v-if="catalogStore.selectedProduct.protection_degree">
                    Степень защиты:
                    {{ catalogStore.selectedProduct.protection_degree }}
                </p>

                <p>
                    Единица продажи:
                    {{ catalogStore.selectedProduct.sales_unit }}
                </p>

                <p v-if="catalogStore.selectedProduct.packaging">
                    Упаковка:
                    {{ catalogStore.selectedProduct.packaging }}
                </p>

                <p v-if="catalogStore.selectedProduct.barcode">
                    Штрихкод:
                    {{ catalogStore.selectedProduct.barcode }}
                </p>
            </section>

            <section v-if="catalogStore.selectedProduct.characteristics.length">
                <h2>Характеристики</h2>

                <ul>
                    <li v-for="characteristic in catalogStore.selectedProduct.characteristics" :key="characteristic.id">
                        <strong>
                            {{ characteristic.name }}:
                        </strong>

                        {{ characteristic.value }}

                        <span v-if="characteristic.unit">
                            {{ characteristic.unit }}
                        </span>
                    </li>
                </ul>
            </section>

            <section v-if="catalogStore.selectedProduct.images.length">
                <h2>Изображения</h2>

                <div>
                    <img v-for="image in catalogStore.selectedProduct.images" :key="image.id" :src="image.image"
                        :alt="catalogStore.selectedProduct.name">
                </div>
            </section>

            <button type="button" :disabled="cartStore.loading" @click="addToCart">
                Добавить в корзину
            </button>
        </template>

        <p v-if="catalogStore.productError">
            Ошибка:
            {{ catalogStore.productError }}
        </p>

        <p v-if="cartStore.error">
            Ошибка корзины:
            {{ cartStore.error }}
        </p>
    </main>
</template>