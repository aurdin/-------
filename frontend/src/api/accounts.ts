import apiClient from './client'

export interface User {
    id: number
    username: string
    email: string
}

export interface RegisterData {
    username: string
    email: string
    password: string
    password_confirm: string
}

export interface LoginData {
    username: string
    password: string
}

export interface CustomerProfile {
    id: number
    first_name: string
    last_name: string
    middle_name: string
    phone: string
    created_at: string
    updated_at: string
}

export interface CustomerAddress {
    id: number
    title: string
    first_name: string
    last_name: string
    middle_name: string
    phone: string
    country: string
    region: string
    city: string
    postal_code: string
    address_line: string
    apartment: string
    is_default: boolean
    created_at: string
    updated_at: string
}

export const register = async (data: RegisterData) => {
    const response = await apiClient.post<User>(
        '/auth/register/',
        data,
    )
    return response.data
}

export const login = async (data: LoginData) => {
    const response = await apiClient.post<User>(
        '/auth/login/',
        data,
    )
    return response.data
}

export const logout = async () => {
    const response = await apiClient.post<{ detail: string }>(
        '/auth/logout/',
    )
    return response.data
}

export const getCurrentUser = async () => {
    const response = await apiClient.get<User>(
        '/auth/me/',
    )
    return response.data
}

export const getProfile = async () => {
    const response = await apiClient.get<CustomerProfile>(
        '/customer/profile/',
    )
    return response.data
}

export const updateProfile = async (
    data: Partial<CustomerProfile>,
) => {
    const response = await apiClient.patch<CustomerProfile>(
        '/customer/profile/',
        data,
    )
    return response.data
}

export const getAddresses = async () => {
    const response = await apiClient.get<CustomerAddress[]>(
        '/customer/addresses/',
    )
    return response.data
}

export const createAddress = async (
    data: Omit<
        CustomerAddress,
        'id' | 'created_at' | 'updated_at'
    >,
) => {
    const response = await apiClient.post<CustomerAddress>(
        '/customer/addresses/',
        data,
    )
    return response.data
}

export const getAddress = async (id: number) => {
    const response = await apiClient.get<CustomerAddress>(
        `/customer/addresses/${id}/`,
    )
    return response.data
}

export const updateAddress = async (
    id: number,
    data: Partial<CustomerAddress>,
) => {
    const response = await apiClient.patch<CustomerAddress>(
        `/customer/addresses/${id}/`,
        data,
    )
    return response.data
}

export const deleteAddress = async (id: number) => {
    await apiClient.delete(`/customer/addresses/${id}/`)
}