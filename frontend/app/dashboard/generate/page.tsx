"use client";

import { useState, useEffect } from 'react';
import { useProducts } from '@/hooks/useProducts';
import { useGeneration } from '@/hooks/useGeneration';
import { ProductSelector } from '@/components/dashboard/ProductSelector';
import { GenerationForm } from '@/components/dashboard/GenerationForm';
import { ResultsGallery } from '@/components/dashboard/ResultsGallery';
import { SpecificationEditor } from '@/components/dashboard/SpecificationEditor';
import { ReferenceImagesPanel } from '@/components/dashboard/ReferenceImagesPanel';
import { Layers, Edit2 } from 'lucide-react';
import { deleteGeneration } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function GeneratePage() {
  const { products, isLoading: isLoadingProducts } = useProducts();
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [isSpecEditorOpen, setIsSpecEditorOpen] = useState(false);
  const { toast } = useToast();
  
  const { 
    generations, 
    isLoadingHistory, 
    isGenerating, 
    fetchHistory, 
    generate 
  } = useGeneration(selectedProductId || undefined);

  // Load history when product is selected
  useEffect(() => {
    if (selectedProductId) {
        fetchHistory();
    }
  }, [selectedProductId, fetchHistory]);

  // Select first product by default if available
  useEffect(() => {
    if (!selectedProductId && products.length > 0) {
        setSelectedProductId(products[0].id);
    }
  }, [products, selectedProductId]);

  const handleGenerate = async (prompt: string, aspectRatio: string) => {
    if (!selectedProductId) return;
    
    // We assume backend handles the logic of merging prompt with specs
    // We send payload
    await generate({
        prompt,
        custom_prompt_override: prompt, // Using the box as override usually
        aspect_ratio: aspectRatio,
        image_count: 1
    });
  };

  const handleDelete = async (generationId: number) => {
    try {
      await deleteGeneration(generationId);
      toast({
        title: "Deleted",
        description: "Generation deleted successfully",
      });
      // Refresh the list
      fetchHistory();
    } catch (error) {
      console.error('Delete failed:', error);
      toast({
        title: "Error",
        description: "Failed to delete generation",
        variant: "destructive",
      });
    }
  };

  const selectedProduct = products.find(p => p.id === selectedProductId);

  return (
    <div className="flex h-full flex-col lg:flex-row overflow-hidden">
      {/* Product Selection Panel */}
      <div className="w-full border-b bg-gray-50 p-4 lg:w-80 lg:border-b-0 lg:border-r lg:overflow-y-auto">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-900">
            <Layers className="h-4 w-4" />
            Products
        </div>
        <ProductSelector
            products={products}
            selectedId={selectedProductId}
            onSelect={setSelectedProductId}
            isLoading={isLoadingProducts}
        />
        
        {/* Specification Editor Button */}
        {selectedProductId && selectedProduct && (
          <div className="mt-6">
            <button
              onClick={() => setIsSpecEditorOpen(true)}
              className="w-full flex items-center justify-center gap-2 rounded-md border border-purple-300 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-100 transition-colors"
            >
              <Edit2 className="h-4 w-4" />
              View/Edit Specification
            </button>
          </div>
        )}
      </div>

      {/* Main Workspace */}
      <div className="flex flex-1 flex-col overflow-hidden bg-gray-100">
        
        {/* Header / Controls */}
        <div className="border-b bg-white px-6 py-4 shadow-sm z-10">
             <div className="mx-auto max-w-5xl">
                {/* Reference Images Panel */}
                {selectedProductId && selectedProduct && (
                  <div className="mb-6">
                    <ReferenceImagesPanel
                      productId={selectedProductId}
                      productSlug={selectedProduct.slug}
                    />
                  </div>
                )}

                <GenerationForm 
                    onGenerate={handleGenerate}
                    isGenerating={isGenerating}
                    disabled={!selectedProductId}
                />
             </div>
        </div>

        {/* Gallery Area */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
            <div className="mx-auto max-w-5xl">
                <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Results Gallery</h2>
                    {generations.length > 0 && (
                        <span className="text-xs text-gray-500">{generations.length} items</span>
                    )}
                </div>
                
                {selectedProductId ? (
                    <ResultsGallery 
                        generations={generations} 
                        isLoading={isLoadingHistory}
                        onDelete={handleDelete}
                    />
                ) : (
                    <div className="flex h-64 items-center justify-center text-gray-400">
                        Select a product to view generations.
                    </div>
                )}
            </div>
        </div>
      </div>

      {/* Specification Editor Modal */}
      {selectedProductId && selectedProduct && (
        <SpecificationEditor
          isOpen={isSpecEditorOpen}
          onClose={() => setIsSpecEditorOpen(false)}
          productId={selectedProductId}
          productSlug={selectedProduct.slug}
          onSaveSuccess={() => {
            // Optionally refresh something
            toast({
              title: 'Success',
              description: 'Specification updated successfully',
            });
          }}
        />
      )}
    </div>
  );
}
