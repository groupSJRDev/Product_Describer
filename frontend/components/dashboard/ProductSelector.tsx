import { Product } from '@/lib/types';
import { Package } from 'lucide-react';

interface ProductSelectorProps {
  products: Product[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  isLoading: boolean;
}

export function ProductSelector({ products, selectedId, onSelect, isLoading }: ProductSelectorProps) {
  if (isLoading) {
    return <div className="h-10 w-full animate-pulse rounded bg-gray-200" />;
  }

  if (products.length === 0) {
    return <div className="text-sm text-gray-500">No products found.</div>;
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">Select Product Context</label>
      <div className="grid grid-cols-1 gap-2">
        {products.map(product => (
          <button
            key={product.id}
            onClick={() => onSelect(product.id)}
            className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${
              selectedId === product.id 
                ? 'border-blue-500 bg-blue-50 text-blue-900 ring-1 ring-blue-500' 
                : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-gray-50'
            }`}
          >
            <div className={`flex h-8 w-8 items-center justify-center rounded-md ${
                selectedId === product.id ? 'bg-blue-200 text-blue-700' : 'bg-gray-100 text-gray-500'
            }`}>
                <Package className="h-4 w-4" />
            </div>
            <div>
                <div className="font-medium">{product.name}</div>
                <div className="text-xs opacity-70 truncate max-w-[200px]">{product.slug}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
