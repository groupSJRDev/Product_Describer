import { LoginForm } from '@/components/auth/LoginForm';
import { Package } from 'lucide-react';

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
            <Package className="h-6 w-6 text-white" />
        </div>
        <span className="text-2xl font-bold text-gray-900">Product Describer</span>
      </div>
      
      <LoginForm />
      
      <p className="mt-8 text-center text-xs text-gray-500">
        &copy; 2026 Product Describer Inc. All rights reserved.
      </p>
    </div>
  );
}
