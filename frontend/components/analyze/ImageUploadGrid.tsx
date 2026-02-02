import { useState, useRef } from 'react';
import { Upload, X, Check } from 'lucide-react';

interface UploadedImage {
  file: File;
  preview: string;
  selected: boolean;
  existingId?: number;
}

interface ImageUploadGridProps {
  images: UploadedImage[];
  onImagesChange: (images: UploadedImage[]) => void;
  onDeleteExisting?: (imageId: number) => Promise<void>;
  maxImages?: number;
  maxSelected?: number;
  requireSelection?: boolean;
}

export function ImageUploadGrid({
  images,
  onImagesChange,
  onDeleteExisting,
  maxImages = 20,
  maxSelected = 4,
  requireSelection = false,
}: ImageUploadGridProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    const newFiles = Array.from(files).slice(0, maxImages - images.length);
    const newImages: UploadedImage[] = newFiles.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      selected: false,
    }));

    onImagesChange([...images, ...newImages]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleRemove = async (index: number) => {
    const imageToRemove = images[index];
    
    // If it's an existing image from DB, call the API to delete it
    if (imageToRemove.existingId && onDeleteExisting) {
      try {
        await onDeleteExisting(imageToRemove.existingId);
      } catch (error) {
        console.error('Failed to delete image:', error);
        return; // Don't remove from UI if API call failed
      }
    }
    
    const newImages = images.filter((_, i) => i !== index);
    onImagesChange(newImages);
  };

  const handleToggleSelect = (index: number) => {
    if (!requireSelection) return; // Don't allow selection if not required
    
    const selectedCount = images.filter((img) => img.selected).length;
    const newImages = [...images];
    
    // If trying to select and already at max, don't allow
    if (!newImages[index].selected && selectedCount >= maxSelected) {
      return;
    }

    newImages[index].selected = !newImages[index].selected;
    onImagesChange(newImages);
  };

  const selectedCount = images.filter((img) => img.selected).length;

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      {images.length < maxImages && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-gray-400'}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
          />
          <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-sm text-gray-600 mb-2">
            Drag and drop images here, or click to browse
          </p>
          <p className="text-xs text-gray-500">
            Upload up to {maxImages} images for analysis
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {images.length} / {maxImages} images uploaded
          </p>
        </div>
      )}

      {/* Selection Counter */}
      {images.length > 0 && requireSelection && (
        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2">
            <Check className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">
              {selectedCount} of {maxSelected} images selected for reference
            </span>
          </div>
          {selectedCount === maxSelected && (
            <span className="text-xs text-blue-600 font-medium">
              Ready to save
            </span>
          )}
          {selectedCount < maxSelected && (
            <span className="text-xs text-gray-600">
              Select {maxSelected - selectedCount} more
            </span>
          )}
        </div>
      )}

      {/* Image Grid */}
      {images.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          {images.map((image, index) => (
            <div
              key={index}
              className={`
                relative group aspect-square rounded-lg overflow-hidden border-2 transition-all
                ${requireSelection ? 'cursor-pointer' : ''}
                ${
                  image.selected && requireSelection
                    ? 'border-blue-500 ring-2 ring-blue-200'
                    : 'border-gray-200 hover:border-gray-300'
                }
              `}
              onClick={() => requireSelection && handleToggleSelect(index)}
            >
              <img
                src={image.preview}
                alt={`Upload ${index + 1}`}
                className="w-full h-full object-cover"
              />

              {/* Selection Indicator */}
              {requireSelection && (
                <div
                  className={`
                    absolute top-2 left-2 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all
                    ${
                      image.selected
                        ? 'bg-blue-600 border-blue-600'
                        : 'bg-white/80 backdrop-blur-sm border-gray-300 group-hover:border-blue-400'
                    }
                  `}
                >
                  {image.selected && <Check className="h-4 w-4 text-white" />}
                </div>
              )}

              {/* Remove Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(index);
                }}
                className="absolute top-2 right-2 p-1.5 bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700"
              >
                <X className="h-3 w-3" />
              </button>

              {/* Image Number */}
              <div className="absolute bottom-2 right-2 px-2 py-0.5 bg-black/50 text-white text-xs rounded backdrop-blur-sm">
                #{index + 1}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
