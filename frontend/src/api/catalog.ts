import apiClient from './client'

export interface CatalogReference {
    id: number
    name: string
}

export interface ProductCharacteristic {
    id: number
    name: string
    value_type: string
    value: string | number | boolean | null
    unit: string | null
    status: boolean
}

export interface ProductImage {
    id: number
    image: string
    status: boolean
}

export interface Product {
    id: number
    article: string
    name: string

    category: CatalogReference | null
    group: CatalogReference | null
    brand: CatalogReference | null
    series: CatalogReference | null
    type: CatalogReference | null
    model: CatalogReference | null
    execution: CatalogReference | null

    protection_degree: string | null
    color: CatalogReference | null

    characteristics: ProductCharacteristic[]

    packaging: string | null
    sales_unit: string
    barcode: string | null

    images: ProductImage[]

    status: boolean
}

export interface ProductListResponse {
    results: Product[]
    message: string | null
}

export interface CatalogFilterItem {
    id: number
    name: string
}

export interface CatalogFilterCharacteristicValue {
    value: string
}

export interface CatalogFilterCharacteristic {
    id: number
    name: string
    value_type: string
    unit: string | null
    values: CatalogFilterCharacteristicValue[]
}

export interface CatalogFilters {
    categories: CatalogFilterItem[]
    groups: CatalogFilterItem[]
    brands: CatalogFilterItem[]
    series: CatalogFilterItem[]
    types: CatalogFilterItem[]
    models: CatalogFilterItem[]
    executions: CatalogFilterItem[]
    colors: CatalogFilterItem[]
    characteristics: CatalogFilterCharacteristic[]
}

export interface ProductListParams {
    search?: string
    category?: number
    group?: number
    brand?: number
    series?: number
    type?: number
    model?: number
    execution?: number
    color?: number
    protection_degree?: string
    article?: string
    characteristic?: string[]
}

export const getProducts = async (
    params?: ProductListParams,
) => {
    const response = await apiClient.get<ProductListResponse>(
        '/products/',
        {
            params,
        },
    )

    return response.data
}

export const getProduct = async (id: number) => {
    const response = await apiClient.get<Product>(
        `/products/${id}/`,
    )

    return response.data
}

export const getCatalogFilters = async () => {
    const response = await apiClient.get<CatalogFilters>(
        '/catalog/filters/',
    )

    return response.data
}