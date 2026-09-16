import { defineStore } from 'pinia'
import {
    getCurrentUser,
    login,
    logout,
    register,
    type LoginData,
    type RegisterData,
    type User,
} from '../api/accounts'

interface AuthState {
    user: User | null
    loading: boolean
    initialized: boolean
    error: string | null
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthState => ({
        user: null,
        loading: false,
        initialized: false,
        error: null,
    }),

    getters: {
        isAuthenticated: (state) => state.user !== null,
    },

    actions: {
        async initialize() {
            if (this.initialized) {
                return
            }

            this.loading = true
            this.error = null

            try {
                this.user = await getCurrentUser()
            } catch {
                this.user = null
            } finally {
                this.loading = false
                this.initialized = true
            }
        },

        async register(data: RegisterData) {
            this.loading = true
            this.error = null

            try {
                this.user = await register(data)
                return this.user
            } catch (error) {
                this.error = 'Не удалось зарегистрировать пользователя.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async login(data: LoginData) {
            this.loading = true
            this.error = null

            try {
                this.user = await login(data)
                return this.user
            } catch (error) {
                this.error = 'Не удалось выполнить вход.'
                throw error
            } finally {
                this.loading = false
            }
        },

        async logout() {
            this.loading = true
            this.error = null

            try {
                await logout()
                this.user = null
            } catch (error) {
                this.error = 'Не удалось выполнить выход.'
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