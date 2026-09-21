import { createRouter, createWebHistory } from 'vue-router'
import CatalogPage from '../views/CatalogPage.vue'
import ProductPage from '../views/ProductPage.vue'

const router = createRouter({
    history: createWebHistory(),

    routes: [
        {
            path: '/',
            name: 'home',
            component: {
                template: '<main><h1>SmEl</h1><p>Smart Electric — frontend</p></main>',
            },
        },
        {
            path: '/catalog',
            name: 'catalog',
            component: CatalogPage,
        },
        {
            path: '/catalog/products/:id',
            name: 'product',
            component: ProductPage,
        },
    ],
})

export default router