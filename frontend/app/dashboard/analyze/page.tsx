"use client";

import { useState } from 'react';
import { useProducts } from '@/hooks/useProducts';
import { ProductSelector } from '@/components/dashboard/ProductSelector';
import { ImageUploadGrid } from '@/components/analyze/ImageUploadGrid';
import { AnalysisProgress } from '@/components/analyze/AnalysisProgress';
import { Sparkles, Layers, Loader2, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { useRouter } from 'next/navigation';

interface UploadedImage {
  file: File;
  preview: string;
  selected: boolean;
  existingId?: number; // ID if this is an existing reference image from DB
}

export default function AnalyzePage() {
  const { products, isLoading: isLoadingProducts, refreshProducts } = useProducts();
  const router = useRouter();
  const [mode, setMode] = useState<'create' | 'existing'>('existing');
  const [newProductName, setNewProductName] = useState('');
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'complete' | 'error'>('idle');
  const [analysisMessage, setAnalysisMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const { toast } = useToast();

  // Select first product by default
  useState(() => {
    if (!selectedProductId && products.length > 0) {
      setSelectedProductId(products[0].id);
    }
  });

  // Load existing reference images when product is selected
  useState(() => {
    if (mode === 'existing' && selectedProductId) {
      loadExistingImages(selectedProductId);
    }
  });

  const loadExistingImages = async (productId: number) => {
    try {
      const response = await api.get(`/products/${productId}/reference-images`);
      const existingImages: UploadedImage[] = response.data.map((img: any) => ({
        file: null as any, // Existing images don't have a File object
        preview: `http://localhost:8001/files/${img.storage_path.replace('local_storage/', '')}`,
        selected: false,
        existingId: img.id,
      }));
      setImages(existingImages);
    } catch (error) {
      console.error('Failed to load existing images:', error);
    }
  };

  const handleProductChange = (productId: number) => {
    setSelectedProductId(productId);
    setImages([]); // Clear images when switching products
    if (mode === 'existing') {
      loadExistingImages(productId);
    }
  };

  const handleDeleteExistingImage = async (imageId: number) => {
    if (!selectedProductId) return;
    
    try {
      await api.delete(`/products/${selectedProductId}/reference-images/${imageId}`);
      toast({
        title: 'Image Deleted',
        description: 'Reference image has been removed.',
      });
    } catch (error) {
      toast({
        title: 'Delete Failed',
        description: 'Failed to delete reference image. Please try again.',
        variant: 'destructive',
      });
      throw error; // Re-throw so the UI knows not to remove it
    }
  };

  const handleDeleteProduct = async () => {
    if (!selectedProductId) return;
    
    const product = products.find(p => p.id === selectedProductId);
    if (!product) return;

    if (!confirm(`Are you sure you want to delete "${product.name}"? This will permanently remove the product and all associated data.`)) {
      return;
    }

    try {
      setIsDeleting(true);
      await api.delete(`/products/${selectedProductId}`);
      
      toast({
        title: 'Product Deleted',
        description: `"${product.name}" has been deleted successfully.`,
      });

      // Reset state
      setSelectedProductId(null);
      setImages([]);
      
      // Refresh products list
      await refreshProducts();
      
    } catch (error: any) {
      console.error('Failed to delete product:', error);
      toast({
        title: 'Delete Failed',
        description: error.response?.data?.detail || 'Failed to delete product. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const selectedProduct = products.find(p => p.id === selectedProductId);
  const selectedImages = images.filter(img => img.selected);
  const canAnalyze = 
    (mode === 'existing' && selectedProductId && images.length > 0) ||
    (mode === 'create' && newProductName.trim() && images.length > 0);

  const handleAnalyze = async () => {
    if (images.length === 0) return;

    let productId = selectedProductId;

    try {
      // Create new product if in create mode
      if (mode === 'create') {
        if (!newProductName.trim()) return;
        
        // Check if product with this name already exists
        const existingProduct = products.find(
          p => p.name.toLowerCase() === newProductName.trim().toLowerCase()
        );
        
        if (existingProduct) {
          toast({
            title: 'Name Already Exists',
            description: `A product named "${existingProduct.name}" already exists. Please choose a unique name.`,
            variant: 'destructive',
          });
          return;
        }
        
        setAnalysisStatus('uploading');
        setProgress(10);
        setAnalysisMessage('Creating product...');

        // Generate base slug
        let slug = newProductName.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
        
        // Try to create with base slug, if conflict, append timestamp
        let createAttempts = 0;
        let createSuccess = false;
        let createResponse;
        
        while (!createSuccess && createAttempts < 3) {
          try {
            const attemptSlug = createAttempts === 0 ? slug : `${slug}_${Date.now()}`;
            createResponse = await api.post('/products', {
              name: newProductName,
              slug: attemptSlug,
            });
            createSuccess = true;
          } catch (err: any) {
            if (err.response?.status === 400 && err.response?.data?.detail?.includes('already exists')) {
              createAttempts++;
              if (createAttempts >= 3) {
                throw new Error(`Unable to create product: ${newProductName} (slug conflict)`);
              }
            } else {
              throw err;
            }
          }
        }

        if (!createResponse) {
          throw new Error('Failed to create product');
        }

        productId = createResponse.data.id;
        await refreshProducts();

        toast({
          title: 'Product Created',
          description: `${newProductName} has been created`,
        });
      }

      if (!productId) return;

      // Delete all existing reference images first to avoid hitting the limit
      try {
        const existingImages = await api.get(`/products/${productId}/reference-images`);
        if (existingImages.data && existingImages.data.length > 0) {
          setAnalysisStatus('uploading');
          setProgress(5);
          setAnalysisMessage('Removing old reference images...');
          
          for (const img of existingImages.data) {
            await api.delete(`/products/${productId}/reference-images/${img.id}`);
          }
        }
      } catch (error) {
        console.warn('Failed to delete old images:', error);
      }

      // Only upload NEW images (not existing ones) - upload ALL for analysis
      const newImagesToUpload = images.filter(img => !img.existingId && img.file);
      
      if (newImagesToUpload.length > 0) {
        setAnalysisStatus('uploading');
        setProgress(20);
        setAnalysisMessage(`Uploading ${newImagesToUpload.length} images for analysis...`);

        let uploadedCount = 0;
        for (const img of newImagesToUpload) {
          const refFormData = new FormData();
          refFormData.append('file', img.file);
          await api.post(`/products/${productId}/reference-images`, refFormData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
          uploadedCount++;
          setProgress(20 + (uploadedCount / newImagesToUpload.length) * 30);
        }
      } else {
        setProgress(20);
      }

      // Give backend a moment to process uploads
      await new Promise(resolve => setTimeout(resolve, 1000));

      setProgress(50);
      
      setAnalysisStatus('analyzing');
      setAnalysisMessage('Running GPT Vision analysis...');

      // Trigger analysis (uses the reference images we just uploaded)
      const response = await api.post(`/products/${productId}/analyze`);

      setProgress(100);
      setAnalysisStatus('complete');
      setAnalysisMessage('Analysis complete! Redirecting to review...');

      toast({
        title: 'Analysis Complete',
        description: `Product specification v${response.data.version} created successfully.`,
      });

      // Redirect to results review page
      setTimeout(() => {
        router.push(`/dashboard/analyze/review?productId=${productId}&specId=${response.data.id}`);
      }, 1000);

    } catch (error: any) {
      console.error('Analysis failed:', error);
      console.error('Error response:', error.response?.data);
      console.error('Full error object:', JSON.stringify(error, null, 2));
      
      let errorMessage = 'Failed to analyze product';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((d: any) => d.msg).join(', ');
        }
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error occurred during analysis. Please check that your OpenAI API key is configured and try again.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setAnalysisStatus('error');
      setAnalysisMessage(errorMessage);
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="flex h-full flex-col lg:flex-row overflow-hidden">
      {/* Product Selection Panel */}
      <div className="w-full border-b bg-gray-50 p-4 lg:w-80 lg:border-b-0 lg:border-r lg:overflow-y-auto">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-900">
          <Layers className="h-4 w-4" />
          Products
        </div>

        {/* Mode Toggle */}
        <div className="mb-4 space-y-2">
          <label className="flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors hover:bg-white">
            <input
              type="radio"
              checked={mode === 'existing'}
              onChange={() => setMode('existing')}
              className="text-blue-600"
            />
            <span className="text-sm font-medium text-gray-700">Use Existing Product</span>
          </label>
          
          <label className="flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors hover:bg-white">
            <input
              type="radio"
              checked={mode === 'create'}
              onChange={() => setMode('create')}
              className="text-blue-600"
            />
            <span className="text-sm font-medium text-gray-700">Create New Product</span>
          </label>
        </div>

        {/* Existing Product Selector */}
        {mode === 'existing' && (
          <div className="space-y-3">
            <ProductSelector
              products={products}
              selectedId={selectedProductId}
              onSelect={handleProductChange}
              isLoading={isLoadingProducts}
            />
            {selectedProductId && (
              <button
                onClick={handleDeleteProduct}
                disabled={isDeleting || analysisStatus === 'uploading' || analysisStatus === 'analyzing'}
                className="flex items-center gap-2 rounded-md border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all w-full justify-center"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Delete Product
                  </>
                )}
              </button>
            )}
          </div>
        )}

        {/* New Product Name Input */}
        {mode === 'create' && (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Product Name
            </label>
            <input
              type="text"
              value={newProductName}
              onChange={(e) => setNewProductName(e.target.value)}
              placeholder="e.g. Stasher Half Gallon"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500">
              A unique name for your product
            </p>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto bg-gray-100 px-6 py-8">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Product Analysis
            </h1>
            <p className="text-sm text-gray-600">
              Upload up to 20 images of your product to analyze. After analysis, you'll select 4 to save as reference images.
            </p>
          </div>

          {/* Image Upload Section */}
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <div className="mb-4 flex items-center gap-2">
              <h2 className="text-lg font-semibold text-gray-900">
                Upload Product Images
              </h2>
              {mode === 'existing' && selectedProduct && (
                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                  {selectedProduct.name}
                </span>
              )}
              {mode === 'create' && newProductName && (
                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                  New: {newProductName}
                </span>
              )}
            </div>

            <ImageUploadGrid
              images={images}
              onImagesChange={setImages}
              onDeleteExisting={handleDeleteExistingImage}
              maxImages={20}
              requireSelection={false}
            />
          </div>

          {/* Analyze Button */}
          {images.length > 0 && analysisStatus !== 'complete' && (
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={handleAnalyze}
                disabled={!canAnalyze || analysisStatus === 'uploading' || analysisStatus === 'analyzing'}
                className="flex items-center gap-2 rounded-md bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 text-sm font-medium text-white hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {analysisStatus === 'uploading' || analysisStatus === 'analyzing' ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Analyze {images.length} Image{images.length !== 1 ? 's' : ''}
                  </>
                )}
              </button>
            </div>
          )}

          {/* Analysis Progress */}
          <AnalysisProgress
            status={analysisStatus}
            progress={progress}
            message={analysisMessage}
          />
        </div>
      </div>
    </div>
  );
}
