import { useState, useEffect, useRef } from 'react';
import { Upload, Loader2, Trash2, Image as ImageIcon } from 'lucide-react';
import { ReferenceImage } from '@/lib/types';
import { 
  getReferenceImages, 
  uploadReferenceImage, 
  deleteReferenceImage 
} from '@/lib/api';
import { getAssetUrl } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface ReferenceImagesPanelProps {
  productId: number;
  productSlug: string;
}

export function ReferenceImagesPanel({
  productId,
  productSlug,
}: ReferenceImagesPanelProps) {
  const [images, setImages] = useState<ReferenceImage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (productId) {
      loadImages();
    }
  }, [productId]);

  const loadImages = async () => {
    setIsLoading(true);
    try {
      const response = await getReferenceImages(productId);
      setImages(response.data);
    } catch (err) {
      console.error('Failed to load reference images', err);
      toast({
        title: 'Error',
        description: 'Failed to load reference images',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadClick = () => {
    if (images.length >= 4) {
      toast({
        title: 'Limit Reached',
        description: 'Maximum of 4 reference images allowed',
        variant: 'destructive',
      });
      return;
    }
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const remainingSlots = 4 - images.length;
    const filesToUpload = Array.from(files).slice(0, remainingSlots);

    if (filesToUpload.length < files.length) {
      toast({
        title: 'Limit Reached',
        description: `Only uploading ${filesToUpload.length} images (max 4 total)`,
      });
    }

    setIsUploading(true);

    try {
      for (const file of filesToUpload) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
          toast({
            title: 'Invalid File',
            description: `${file.name} is not an image file`,
            variant: 'destructive',
          });
          continue;
        }

        await uploadReferenceImage(productId, file);
      }

      toast({
        title: 'Uploaded',
        description: `${filesToUpload.length} image(s) uploaded successfully`,
      });

      // Reload images
      await loadImages();
    } catch (err: any) {
      console.error('Failed to upload images', err);
      const errorMsg = err.response?.data?.detail || 'Failed to upload images';
      toast({
        title: 'Error',
        description: errorMsg,
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (imageId: number) => {
    if (!confirm('Are you sure you want to delete this reference image?')) {
      return;
    }

    setDeletingId(imageId);
    try {
      await deleteReferenceImage(productId, imageId);
      
      toast({
        title: 'Deleted',
        description: 'Reference image deleted successfully',
      });

      // Reload images
      await loadImages();
    } catch (err: any) {
      console.error('Failed to delete image', err);
      const errorMsg = err.response?.data?.detail || 'Failed to delete image';
      toast({
        title: 'Error',
        description: errorMsg,
        variant: 'destructive',
      });
    } finally {
      setDeletingId(null);
    }
  };

  const handleImageClick = (image: ReferenceImage) => {
    // Open image in new tab
    const url = getAssetUrl(image.storage_path);
    window.open(url, '_blank');
  };

  // Create placeholder slots
  const slots = Array.from({ length: 4 }, (_, i) => images[i] || null);

  return (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-2 flex items-center justify-between flex-shrink-0">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-gray-900">
            Reference Images
          </h3>
          <p className="text-xs text-gray-500 truncate">
            Max 4 images for generation context
          </p>
        </div>
        <button
          onClick={handleUploadClick}
          disabled={isUploading || images.length >= 4}
          className="flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
        >
          {isUploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              Upload Images
            </>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center text-gray-500 py-8">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          <span className="text-sm">Loading...</span>
        </div>
      ) : (
        <div className="flex gap-3 flex-wrap">
          {slots.map((image, index) => (
            <div
              key={image?.id || `empty-${index}`}
              className="group relative overflow-hidden rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 transition-all flex-shrink-0"
              style={{
                width: '100px',
                height: '100px'
              }}
            >
              {image ? (
                <>
                  <img
                    src={getAssetUrl(image.storage_path)}
                    alt={image.filename}
                    className="h-full w-full cursor-pointer object-cover transition-opacity hover:opacity-75"
                    onClick={() => handleImageClick(image)}
                  />
                  <div 
                    className="absolute left-2 top-2 rounded-full bg-purple-600 px-2 py-0.5 text-xs font-medium text-white"
                  >
                    {index + 1}
                  </div>
                  <button
                    onClick={() => handleDelete(image.id)}
                    disabled={deletingId === image.id}
                    className="absolute right-2 top-2 z-50 rounded-full bg-red-600 p-1 text-white opacity-0 transition-all hover:bg-red-700 group-hover:opacity-100 disabled:cursor-not-allowed"
                  >
                    {deletingId === image.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                  </button>
                </>
              ) : (
                <div className="flex h-full flex-col items-center justify-center text-gray-400">
                  <ImageIcon className="h-8 w-8 mb-1" />
                  <span className="text-xs">Slot {index + 1}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {images.length === 0 && !isLoading && (
        <div className="mt-4 text-center text-sm text-gray-500">
          No reference images yet. Upload up to 4 images to use in generation.
        </div>
      )}
    </div>
  );
}
