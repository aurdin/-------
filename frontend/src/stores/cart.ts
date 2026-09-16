import { defineStore } from 'pinia'
import {
    addCartItem,
    clearCart,
    getCart,
    removeCartItem,
    updateCartItem,
    type AddCartItemData,
    type Cart,
    type UpdateCartItemData,
} from '../api/cart'

interface CartState {
    cart: Cart | null
    loading: boolean
    error: string | null
}

export const useCartStore = defineStore('cart', {
    state: (): CartState => ({
        cart: null,
        loading: false,
        error: null,
    }),

    getters: {
        items: (state) => state.cart?.items ?? [],

        itemsCount: (state) =>
            state.cart?.items.reduce(
                (total, item) => total + Number(item.quantity),
                0,
            ) ?? 0,

        isEmpty: (state) =>
            !state.cart || state.cart.items.length === 0,
    },

    actions: {
        async fetchCart() {
            this.loading = true
            this.error = null

            try {
                this.cart = await getCart()
                return this.cart
            } catch (error) {
                this.error = 'Не удалось загрузить корзину.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async addItem(data: AddCartItemData) {
            this.loading = true
            this.error = null

            try {
                await addCartItem(data)
                await this.fetchCart()
                return this.cart
            } catch (error) {
                this.error = 'Не удалось добавить товар в корзину.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async updateItem(
            id: number,
            data: UpdateCartItemData,
        ) {
            this.loading = true
            this.error = null

            try {
                await updateCartItem(id, data)
                await this.fetchCart()
                return this.cart
            } catch (error) {
                this.error = 'Не удалось изменить товар в корзине.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async removeItem(id: number) {
            this.loading = true
            this.error = null

            try {
                await removeCartItem(id)
                await this.fetchCart()
                return this.cart
            } catch (error) {
                this.error = 'Не удалось удалить товар из корзины.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async clear() {
            this.loading = true
            this.error = null

            try {
                await clearCart()
                await this.fetchCart()
                return this.cart
            } catch (error) {
                this.error = 'Не удалось очистить корзину.'
                throw error
            } finally {
                this.loading = false
            }
        },

        clearError() {
            this.error = null
        },
    },
})