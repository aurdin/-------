import axios from 'axios'

const getCsrfToken = () => {
    const cookie = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='))

    return cookie
        ? decodeURIComponent(cookie.split('=')[1])
        : null
}

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    withCredentials: true,
})

apiClient.interceptors.request.use((config) => {
    const method = config.method?.toLowerCase()

    if (
        method === 'post' ||
        method === 'put' ||
        method === 'patch' ||
        method === 'delete'
    ) {
        const csrfToken = getCsrfToken()

        if (csrfToken) {
            config.headers.set('X-CSRFToken', csrfToken)
        }
    }

    return config
})

export default apiClient