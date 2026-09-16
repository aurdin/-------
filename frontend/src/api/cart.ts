import apiClient from './client'

export interface CartProduct {
    id: number
    article: string
}

export interface CartItem {
    id: number
    product: CartProduct
    product_id?: number
    quantity: number
    created_at: string
    updated_at: string
}

export interface Cart {
    id: number
    status: boolean
    items: CartItem[]
    created_at: string
    updated_at: string
}

export interface AddCartItemData {
    product_id: number
    quantity: number
}

export interface UpdateCartItemData {
    quantity: number
}

export const getCart = async () => {
    const response = await apiClient.get<Cart>('/cart/')
    return response.data
}

export const clearCart = async () => {
    await apiClient.delete('/cart/')
}

export const addCartItem = async (
    data: AddCartItemData,
) => {
    const response = await apiClient.post<CartItem>(
        '/cart/items/',
        data,
    )
    return response.data
}

export const updateCartItem = async (
    id: number,
    data: UpdateCartItemData,
) => {
    const response = await apiClient.patch<CartItem>(
        `/cart/items/${id}/`,
        data,
    )
    return response.data
}

export const removeCartItem = async (id: number) => {
    await apiClient.delete(`/cart/items/${id}/`)
}