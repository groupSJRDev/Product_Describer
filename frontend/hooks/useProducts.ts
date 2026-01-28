import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Product } from '@/lib/types';

export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<Product[]>('/products');
      setProducts(response.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch products');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return { products, isLoading, error, refreshProducts: fetchProducts };
}
