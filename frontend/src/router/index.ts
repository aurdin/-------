import { createRouter, createWebHistory } from 'vue-router'

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
    ],
})

export default router
