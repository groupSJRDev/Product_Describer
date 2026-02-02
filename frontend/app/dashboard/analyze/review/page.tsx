"use client";

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { CheckCircle2, Save, ArrowLeft, Loader2, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import * as yaml from 'js-yaml';
import type { Product, Specification } from '@/lib/types';

interface UploadedImage {
  id: number;
  filename: string;
  storage_path: string;
  preview: string;
  selected: boolean;
}

function ReviewPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const productId = searchParams.get('productId');
  const specId = searchParams.get('specId');
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [product, setProduct] = useState<Product | null>(null);
  const [specification, setSpecification] = useState<Specification | null>(null);
  const [yamlSections, setYamlSections] = useState<Record<string, unknown>>({});
  const [enabledSections, setEnabledSections] = useState<Record<string, boolean>>({});
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [images, setImages] = useState<UploadedImage[]>([]);

  useEffect(() => {
    if (productId && specId) {
      loadData();
    }
  }, [productId, specId]);

  const loadData = async () => {
    try {
      setIsLoading(true);

      // Load product
      const productResponse = await api.get(`/products/${productId}`);
      setProduct(productResponse.data);

      // Load specification
      const specResponse = await api.get(`/products/${productId}/specifications/${specId}`);
      setSpecification(specResponse.data);

      // Parse YAML
      const parsedYaml = yaml.load(specResponse.data.yaml_content) as Record<string, unknown>;
      setYamlSections(parsedYaml || {});

      // Initialize all sections as enabled
      const sections: Record<string, boolean> = {};
      Object.keys(parsedYaml || {}).forEach(key => {
        sections[key] = true;
      });
      setEnabledSections(sections);

      // Load reference images
      const imagesResponse = await api.get(`/products/${productId}/reference-images`);
      const loadedImages: UploadedImage[] = imagesResponse.data.map((img: { id: number; filename: string; storage_path: string }) => ({
        id: img.id,
        filename: img.filename,
        storage_path: img.storage_path,
        preview: `http://localhost:8001/files/${img.storage_path}`,
        selected: false,
      }));
      setImages(loadedImages);

    } catch (error) {
      console.error('Failed to load data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load analysis results',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleSection = (section: string) => {
    setEnabledSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleToggleExpanded = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleToggleImage = (index: number) => {
    const selectedCount = images.filter(img => img.selected).length;
    const newImages = [...images];
    
    // If trying to select and already at 4, don't allow
    if (!newImages[index].selected && selectedCount >= 4) {
      toast({
        title: 'Maximum Reached',
        description: 'You can only select 4 reference images',
        variant: 'destructive',
      });
      return;
    }

    newImages[index].selected = !newImages[index].selected;
    setImages(newImages);
  };

  const handleSave = async () => {
    const selectedImages = images.filter(img => img.selected);
    
    if (selectedImages.length !== 4) {
      toast({
        title: 'Invalid Selection',
        description: 'Please select exactly 4 images',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsSaving(true);

      // Build filtered YAML with only enabled sections
      const filteredYaml: Record<string, unknown> = {};
      Object.keys(yamlSections).forEach(key => {
        if (enabledSections[key]) {
          filteredYaml[key] = yamlSections[key];
        }
      });

      // Update specification with filtered YAML
      const yamlContent = yaml.dump(filteredYaml, { sortKeys: false });
      await api.put(`/specifications/${specId}`, {
        yaml_content: yamlContent,
        change_notes: 'Filtered sections and selected reference images',
      });

      // Delete non-selected images
      const imagesToDelete = images.filter(img => !img.selected);
      for (const img of imagesToDelete) {
        await api.delete(`/products/${productId}/reference-images/${img.id}`);
      }

      toast({
        title: 'Success',
        description: 'Analysis results saved successfully!',
      });

      // Redirect back to analyze page
      router.push('/dashboard/analyze');
    } catch (error) {
      console.error('Failed to save:', error);
      toast({
        title: 'Save Failed',
        description: 'Failed to save results. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!confirm(`Are you sure you want to delete "${product?.name}"? This will permanently delete the product and all associated data.`)) {
      return;
    }

    try {
      setIsDeleting(true);

      await api.delete(`/products/${productId}`);

      toast({
        title: 'Product Deleted',
        description: `"${product?.name}" has been deleted successfully.`,
      });

      // Redirect back to analyze page
      router.push('/dashboard/analyze');
    } catch (error) {
      console.error('Failed to delete product:', error);
      toast({
        title: 'Delete Failed',
        description: 'Failed to delete product. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const selectedCount = images.filter(img => img.selected).length;
  const canSave = selectedCount === 4;

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gray-100">
      {/* Header */}
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Review Analysis Results
              </h1>
              <p className="text-sm text-gray-600">
                {product?.name} - Specification v{specification?.version}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleDeleteProduct}
              disabled={isDeleting || isSaving}
              className="flex items-center gap-2 rounded-md border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
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
            <button
              onClick={handleSave}
              disabled={!canSave || isSaving || isDeleting}
              className="flex items-center gap-2 rounded-md bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-2 text-sm font-medium text-white hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Results
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto max-w-6xl space-y-6">
          {/* Image Selection */}
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              Select Reference Images ({selectedCount}/4)
            </h2>
            <p className="mb-4 text-sm text-gray-600">
              Select exactly 4 images to save as reference images for this product.
            </p>
            <div className="grid grid-cols-5 gap-4">
              {images.map((image, index) => (
                <div
                  key={image.id}
                  onClick={() => handleToggleImage(index)}
                  className={`
                    relative aspect-square cursor-pointer rounded-lg border-2 transition-all overflow-hidden
                    ${image.selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200 hover:border-gray-300'}
                  `}
                >
                  <img
                    src={image.preview}
                    alt={image.filename}
                    className="w-full h-full object-cover"
                  />
                  {image.selected && (
                    <div className="absolute inset-0 bg-blue-500 bg-opacity-20 flex items-center justify-center">
                      <CheckCircle2 className="h-8 w-8 text-blue-600" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* YAML Sections */}
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              Specification Sections
            </h2>
            <p className="mb-4 text-sm text-gray-600">
              Toggle sections to include or exclude them from the final specification.
            </p>
            <div className="space-y-3">
              {Object.keys(yamlSections).map(section => (
                <div
                  key={section}
                  className="rounded-lg border overflow-hidden"
                >
                  <label
                    className="flex items-center gap-3 p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={enabledSections[section] || false}
                      onChange={() => handleToggleSection(section)}
                      className="h-5 w-5 text-blue-600 rounded"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{section}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {typeof yamlSections[section] === 'object' && yamlSections[section] !== null && !Array.isArray(yamlSections[section])
                          ? `${Object.keys(yamlSections[section] as object).length} properties`
                          : typeof yamlSections[section]}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        handleToggleExpanded(section);
                      }}
                      className="p-2 hover:bg-gray-100 rounded transition-colors"
                    >
                      {expandedSections[section] ? (
                        <ChevronUp className="h-4 w-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                      )}
                    </button>
                  </label>
                  {expandedSections[section] && (
                    <div className="border-t bg-gray-50 p-4">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                        {typeof yamlSections[section] === 'object'
                          ? JSON.stringify(yamlSections[section], null, 2)
                          : String(yamlSections[section])}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense fallback={
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    }>
      <ReviewPageContent />
    </Suspense>
  );
}
