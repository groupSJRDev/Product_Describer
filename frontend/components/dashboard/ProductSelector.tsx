import { Product } from '@/lib/types';
import { Package, ChevronDown } from 'lucide-react';

interface ProductSelectorProps {
  products: Product[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  isLoading: boolean;
}

export function ProductSelector({ products, selectedId, onSelect, isLoading }: ProductSelectorProps) {
  const selectedProduct = products.find(p => p.id === selectedId);

  if (isLoading) {
    return <div className="h-24 w-full animate-pulse rounded-lg bg-gray-200" />;
  }

  if (products.length === 0) {
    return <div className="text-sm text-gray-500">No products found.</div>;
  }

  return (
    <div className="space-y-4">
      {/* Active Product Display */}
      {selectedProduct && (
        <div className="rounded-lg border-2 border-blue-500 bg-blue-50 p-4">
          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-blue-600">
            Active Product Context
          </div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-200 text-blue-700">
              <Package className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-blue-900">{selectedProduct.name}</div>
              <div className="text-xs text-blue-700 truncate">{selectedProduct.slug}</div>
            </div>
          </div>
        </div>
      )}

      {/* Product Selector Dropdown */}
      <div>
        <label htmlFor="product-select" className="mb-2 block text-sm font-medium text-gray-700">
          Switch Product
        </label>
        <div className="relative">
          <select
            id="product-select"
            value={selectedId || ''}
            onChange={(e) => onSelect(Number(e.target.value))}
            className="w-full appearance-none rounded-lg border border-gray-300 bg-white px-4 py-2.5 pr-10 text-sm font-medium text-gray-900 transition-colors hover:border-gray-400 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
          >
            {products.map(product => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <ChevronDown className="h-4 w-4 text-gray-500" />
          </div>
        </div>
      </div>
    </div>
  );
}
