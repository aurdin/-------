<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import AuthPanel from './components/AuthPanel.vue'
import CartPanel from './components/CartPanel.vue'
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
    <header>
        <h1>SmEl</h1>
        <p>Smart Electric — frontend</p>

        <nav>
            <RouterLink to="/">
                Главная
            </RouterLink>

            |

            <RouterLink to="/catalog">
                Каталог
            </RouterLink>
        </nav>
    </header>

    <hr>

    <RouterView />

    <hr>

    <AuthPanel />

    <hr>

    <CartPanel />
</template>