<script setup lang="ts">
import CartItem from './CartItem.vue'
import { useCartStore } from '../stores/cart'

const cartStore = useCartStore()
</script>

<template>
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
                <CartItem v-for="item in cartStore.items" :key="item.id" :item="item" :loading="cartStore.loading"
                    @increase="
                        cartStore.updateItem(item.id, {
                            quantity: Number(item.quantity) + 1,
                        })
                        " @decrease="
                        cartStore.updateItem(item.id, {
                            quantity: Number(item.quantity) - 1,
                        })
                        " @remove="cartStore.removeItem(item.id)" />
            </ul>
        </template>

        <p v-if="cartStore.error">
            Ошибка: {{ cartStore.error }}
        </p>

        <button type="button" :disabled="cartStore.loading" @click="
            cartStore.addItem({
                product_id: 15,
                quantity: 2,
            })
            ">
            Добавить TEST-STOCK-001 × 2
        </button>

        <button type="button" :disabled="cartStore.loading || cartStore.isEmpty" @click="cartStore.clear()">
            Очистить корзину
        </button>
    </section>
</template>