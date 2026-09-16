<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')

const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')

const asyncError = ref<string | null>(null)

const submit = async () => {
    asyncError.value = null
    authStore.clearError()

    try {
        if (mode.value === 'login') {
            await authStore.login({
                username: username.value,
                password: password.value,
            })
        } else {
            await authStore.register({
                username: username.value,
                email: email.value,
                password: password.value,
                password_confirm: passwordConfirm.value,
            })
        }

        password.value = ''
        passwordConfirm.value = ''
    } catch (error: any) {
        const data = error?.response?.data

        if (data && typeof data === 'object') {
            asyncError.value = Object.entries(data)
                .map(([field, messages]) => {
                    if (Array.isArray(messages)) {
                        return `${field}: ${messages.join(', ')}`
                    }

                    return `${field}: ${String(messages)}`
                })
                .join(' ')
        } else {
            asyncError.value = 'Произошла ошибка.'
        }
    }
}

const handleLogout = async () => {
    asyncError.value = null

    try {
        await authStore.logout()
    } catch {
        // Ошибка уже записана в authStore.
    }
}

const switchMode = () => {
    mode.value = mode.value === 'login'
        ? 'register'
        : 'login'

    asyncError.value = null
    authStore.clearError()
}
</script>

<template>
    <section>
        <h2>Авторизация</h2>

        <template v-if="authStore.isAuthenticated">
            <p>
                Вы вошли как:
                <strong>{{ authStore.user?.username }}</strong>
            </p>

            <p>
                Email:
                {{ authStore.user?.email }}
            </p>

            <button type="button" :disabled="authStore.loading" @click="handleLogout">
                Выйти
            </button>
        </template>

        <template v-else>
            <h3>
                {{
                    mode === 'login'
                        ? 'Вход'
                        : 'Регистрация'
                }}
            </h3>

            <form @submit.prevent="submit">
                <div>
                    <label for="username">
                        Логин
                    </label>

                    <input id="username" v-model="username" type="text" autocomplete="username" required>
                </div>

                <div v-if="mode === 'register'">
                    <label for="email">
                        Email
                    </label>

                    <input id="email" v-model="email" type="email" autocomplete="email" required>
                </div>

                <div>
                    <label for="password">
                        Пароль
                    </label>

                    <input id="password" v-model="password" type="password" :autocomplete="mode === 'login'
                            ? 'current-password'
                            : 'new-password'
                        " required>
                </div>

                <div v-if="mode === 'register'">
                    <label for="password-confirm">
                        Повторите пароль
                    </label>

                    <input id="password-confirm" v-model="passwordConfirm" type="password" autocomplete="new-password"
                        required>
                </div>

                <button type="submit" :disabled="authStore.loading">
                    {{
                        authStore.loading
                            ? 'Подождите...'
                            : mode === 'login'
                                ? 'Войти'
                                : 'Зарегистрироваться'
                    }}
                </button>
            </form>

            <p v-if="authStore.error">
                {{ authStore.error }}
            </p>

            <p v-if="asyncError">
                {{ asyncError }}
            </p>

            <button type="button" @click="switchMode">
                {{
                    mode === 'login'
                        ? 'Создать аккаунт'
                        : 'У меня уже есть аккаунт'
                }}
            </button>
        </template>
    </section>
</template>