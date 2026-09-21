import { defineStore } from 'pinia'
import {
    getCatalogFilters,
    getProduct,
    getProducts,
    type CatalogFilters,
    type Product,
    type ProductListParams,
} from '../api/catalog'

interface CatalogState {
    products: Product[]
    filters: CatalogFilters | null
    selectedProduct: Product | null
    loading: boolean
    loadingProduct: boolean
    loadingFilters: boolean
    error: string | null
    filtersError: string | null
    productError: string | null
    message: string | null
}

export const useCatalogStore = defineStore('catalog', {
    state: (): CatalogState => ({
        products: [],
        filters: null,
        selectedProduct: null,

        loading: false,
        loadingProduct: false,
        loadingFilters: false,

        error: null,
        filtersError: null,
        productError: null,

        message: null,
    }),

    getters: {
        productsCount: (state) => state.products.length,

        isEmpty: (state) => state.products.length === 0,

        hasFilters: (state) => state.filters !== null,
    },

    actions: {
        async fetchProducts(params?: ProductListParams) {
            this.loading = true
            this.error = null
            this.message = null

            try {
                const response = await getProducts(params)

                this.products = response.results
                this.message = response.message

                return this.products
            } catch (error) {
                this.error = 'Не удалось загрузить товары.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async fetchProduct(id: number) {
            this.loadingProduct = true
            this.productError = null

            try {
                this.selectedProduct = await getProduct(id)
                return this.selectedProduct
            } catch (error) {
                this.productError = 'Не удалось загрузить товар.'
                throw error
            } finally {
                this.loadingProduct = false
            }
        },

        async fetchFilters() {
            this.loadingFilters = true
            this.filtersError = null

            try {
                this.filters = await getCatalogFilters()
                return this.filters
            } catch (error) {
                this.filtersError = 'Не удалось загрузить фильтры каталога.'
                throw error
            } finally {
                this.loadingFilters = false
            }
        },

        clearSelectedProduct() {
            this.selectedProduct = null
            this.productError = null
        },

        clearErrors() {
            this.error = null
            this.filtersError = null
            this.productError = null
        },
    },
})