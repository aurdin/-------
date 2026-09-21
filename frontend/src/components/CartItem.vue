<script setup lang="ts">
import type { CartItem as CartItemType } from '../api/cart'

defineProps<{
    item: CartItemType
    loading: boolean
}>()

const emit = defineEmits<{
    increase: []
    decrease: []
    remove: []
}>()
</script>

<template>
    <li>
        {{ item.product.article }}
        — {{ item.quantity }} шт.

        <button type="button" :disabled="loading" @click="emit('increase')">
            +1
        </button>

        <button type="button" :disabled="loading || Number(item.quantity) <= 1" @click="emit('decrease')">
            -1
        </button>

        <button type="button" :disabled="loading" @click="emit('remove')">
            Удалить
        </button>
    </li>
</template>