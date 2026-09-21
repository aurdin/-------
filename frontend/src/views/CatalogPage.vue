<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useCartStore } from '../stores/cart'
import { useCatalogStore } from '../stores/catalog'
import { RouterLink } from 'vue-router'

const catalogStore = useCatalogStore()
const cartStore = useCartStore()

const search = ref('')
const selectedCategory = ref<number | undefined>(undefined)
const selectedGroup = ref<number | undefined>(undefined)
const selectedType = ref<number | undefined>(undefined)

const loadProducts = async () => {
    const value = search.value.trim()

    await catalogStore.fetchProducts({
        ...(value ? { search: value } : {}),
        ...(selectedCategory.value
            ? { category: selectedCategory.value }
            : {}),
        ...(selectedGroup.value
            ? { group: selectedGroup.value }
            : {}),
        ...(selectedType.value
            ? { type: selectedType.value }
            : {}),
    })
}

const addToCart = async (productId: number) => {
    await cartStore.addItem({
        product_id: productId,
        quantity: 1,
    })
}

const clearFilters = async () => {
    search.value = ''
    selectedCategory.value = undefined
    selectedGroup.value = undefined
    selectedType.value = undefined

    await loadProducts()
}

onMounted(async () => {
    await catalogStore.fetchFilters()
    await loadProducts()
})
</script>

<template>
    <main>
        <h1>Каталог</h1>

        <section>
            <h2>Поиск и фильтры</h2>

            <form @submit.prevent="loadProducts">
                <div>
                    <label for="catalog-search">
                        Поиск
                    </label>

                    <input id="catalog-search" v-model="search" type="search"
                        placeholder="Артикул, тип, модель, бренд...">
                </div>

                <div v-if="catalogStore.filters">
                    <label for="catalog-category">
                        Категория
                    </label>

                    <select id="catalog-category" v-model="selectedCategory">
                        <option :value="undefined">
                            Все категории
                        </option>

                        <option v-for="item in catalogStore.filters.categories" :key="item.id" :value="item.id">
                            {{ item.name }}
                        </option>
                    </select>
                </div>

                <div v-if="catalogStore.filters">
                    <label for="catalog-group">
                        Группа
                    </label>

                    <select id="catalog-group" v-model="selectedGroup">
                        <option :value="undefined">
                            Все группы
                        </option>

                        <option v-for="item in catalogStore.filters.groups" :key="item.id" :value="item.id">
                            {{ item.name }}
                        </option>
                    </select>
                </div>

                <div v-if="catalogStore.filters">
                    <label for="catalog-type">
                        Тип
                    </label>

                    <select id="catalog-type" v-model="selectedType">
                        <option :value="undefined">
                            Все типы
                        </option>

                        <option v-for="item in catalogStore.filters.types" :key="item.id" :value="item.id">
                            {{ item.name }}
                        </option>
                    </select>
                </div>

                <button type="submit" :disabled="catalogStore.loading">
                    Найти
                </button>

                <button type="button" :disabled="catalogStore.loading" @click="clearFilters">
                    Сбросить
                </button>
            </form>
        </section>

        <p v-if="catalogStore.loading">
            Загрузка товаров...
        </p>

        <template v-else>
            <p>
                Найдено товаров:
                {{ catalogStore.productsCount }}
            </p>

            <p v-if="catalogStore.message">
                {{ catalogStore.message }}
            </p>

            <section v-if="!catalogStore.isEmpty">
                <article v-for="product in catalogStore.products" :key="product.id">
                    <h2>
                        <RouterLink :to="`/catalog/products/${product.id}`">
                            {{ product.name }}
                        </RouterLink>
                    </h2>

                    <p>
                        Артикул:
                        {{ product.article }}
                    </p>

                    <p v-if="product.category">
                        Категория:
                        {{ product.category.name }}
                    </p>

                    <p v-if="product.group">
                        Группа:
                        {{ product.group.name }}
                    </p>

                    <p v-if="product.type">
                        Тип:
                        {{ product.type.name }}
                    </p>

                    <p>
                        Единица продажи:
                        {{ product.sales_unit }}
                    </p>

                    <button type="button" :disabled="cartStore.loading" @click="addToCart(product.id)">
                        Добавить в корзину
                    </button>
                </article>
            </section>
        </template>

        <p v-if="catalogStore.error">
            Ошибка:
            {{ catalogStore.error }}
        </p>

        <p v-if="catalogStore.filtersError">
            Ошибка фильтров:
            {{ catalogStore.filtersError }}
        </p>

        <p v-if="cartStore.error">
            Ошибка корзины:
            {{ cartStore.error }}
        </p>
    </main>
</template>