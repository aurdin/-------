<script setup lang="ts">
import { onMounted } from 'vue'
import AuthPanel from './components/AuthPanel.vue'
import { useAuthStore } from './stores/auth'
import { useCartStore } from './stores/cart'

const authStore = useAuthStore()
const cartStore = useCartStore()

onMounted(async () => {
    await authStore.initialize()
    await cartStore.fetchCart()
})
</script>

<template>
    <main>
        <h1>SmEl</h1>
        <p>Smart Electric — frontend</p>

        <hr>

        <AuthPanel />

        <hr>

        <section>
            <h2>Корзина</h2>

            <p v-if="cartStore.loading">
                Загрузка корзины...
            </p>

            <template v-else>
                <p>
                    ID корзины:
                    {{ cartStore.cart?.id ?? '—' }}
                </p>

                <p>
                    Товаров:
                    {{ cartStore.itemsCount }}
                </p>

                <p v-if="cartStore.isEmpty">
                    Корзина пуста.
                </p>

                <ul v-else>
                    <li v-for="item in cartStore.items" :key="item.id">
                        {{ item.product.article }}
                        — {{ item.quantity }} шт.

                        <button type="button" :disabled="cartStore.loading" @click="cartStore.updateItem(item.id, {
                            quantity: Number(item.quantity) + 1,
                        })">
                            +1
                        </button>

                        <button type="button" :disabled="cartStore.loading ||
                            Number(item.quantity) <= 1
                            " @click="cartStore.updateItem(item.id, {
                                quantity: Number(item.quantity) - 1,
                            })">
                            -1
                        </button>
                        <button type="button" :disabled="cartStore.loading" @click="cartStore.removeItem(item.id)">
                            Удалить
                        </button>
                    </li>
                </ul>
            </template>

            <p v-if="cartStore.error">
                Ошибка: {{ cartStore.error }}
            </p>

            <button type="button" :disabled="cartStore.loading" @click="cartStore.addItem({
                product_id: 15,
                quantity: 2,
            })">
                Добавить TEST-STOCK-001 × 2
            </button>
            <button type="button" :disabled="cartStore.loading || cartStore.isEmpty" @click="cartStore.clear()">
                Очистить корзину
            </button>
        </section>
    </main>
</template>