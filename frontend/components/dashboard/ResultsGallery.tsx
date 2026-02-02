import { GenerationRequest } from '@/lib/types';
import { getAssetUrl } from '@/lib/api';
import { Loader2, AlertCircle, ImageIcon, Download, Maximize2, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface ResultsGalleryProps {
  generations: GenerationRequest[];
  isLoading: boolean;
  onDelete?: (generationId: number) => void;
}

export function ResultsGallery({ generations, isLoading, onDelete }: ResultsGalleryProps) {
  if (isLoading && generations.length === 0) {
    return (
        <div className="flex h-64 items-center justify-center text-gray-400">
            <Loader2 className="h-8 w-8 animate-spin" />
        </div>
    );
  }

  if (generations.length === 0) {
    return (
        <div className="flex h-64 flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 text-gray-400">
            <ImageIcon className="h-10 w-10 mb-2 opacity-50" />
            <p className="text-sm">No generations yet.</p>
        </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {generations.map((gen) => (
        <GenerationCard key={gen.id} generation={gen} onDelete={onDelete} />
      ))}
    </div>
  );
}

function GenerationCard({ generation, onDelete }: { generation: GenerationRequest; onDelete?: (id: number) => void }) {
    const isCompleted = generation.status === 'completed';
    const isFailed = generation.status === 'failed';
    const isProcessing = generation.status === 'processing' || generation.status === 'pending';
    
    // Get generated images
    const images = generation.generated_images;
    const hasImages = images && images.length > 0;
    const imageUrl = hasImages ? getAssetUrl(images[0].storage_path) : '';
    
    // Function to handle delete
    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        console.log('Delete clicked for generation:', generation.id);
        if (onDelete && confirm('Delete this generation? This cannot be undone.')) {
            console.log('User confirmed delete');
            onDelete(generation.id);
        } else {
            console.log('Delete cancelled or no handler');
        }
    };
    
    // Function to handle download
    const handleDownload = async () => {
        if (!imageUrl) return;
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            // Extract filename from path or use ID
            const filename = imageUrl.split('/').pop() || `generation-${generation.id}.png`;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Download failed:', error);
            // Fallback: just open in new tab if blob fails (e.g. CORS)
            window.open(imageUrl, '_blank');
        }
    };

    return (
        <Dialog>
        <div className="group relative overflow-hidden rounded-lg border bg-white shadow-sm transition-shadow hover:shadow-md">
            {/* Delete button - positioned absolutely on card */}
            <button
                onClick={handleDelete}
                className="absolute top-2 right-2 z-50 opacity-0 group-hover:opacity-100 transition-opacity bg-red-500 hover:bg-red-600 text-white p-1.5 rounded-md shadow-lg hover:scale-110"
                title={isProcessing ? "Cancel generation" : "Delete"}
                type="button"
            >
                <Trash2 className="h-4 w-4" />
            </button>
            
            <div className="aspect-square w-full relative bg-gray-100">
                {isProcessing && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-blue-500 bg-white/50 backdrop-blur-sm z-10 pointer-events-none">
                        <Loader2 className="h-8 w-8 animate-spin mb-2" />
                        <span className="text-xs font-semibold tracking-wider uppercase">Processing</span>
                    </div>
                )}
                
                {isFailed && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-red-500 bg-red-50 pointer-events-none">
                        <AlertCircle className="h-8 w-8 mb-2" />
                        <span className="text-xs font-semibold">Failed</span>
                    </div>
                )}

                {isCompleted && hasImages ? (
                    <DialogTrigger asChild>
                        <div className="relative h-full w-full cursor-pointer">
                            <img 
                                src={imageUrl} 
                                alt={generation.prompt}
                                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                                loading="lazy"
                            />
                            {/* Overlay icon on hover */}
                            <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors group-hover:bg-black/20 opacity-0 group-hover:opacity-100">
                                <Maximize2 className="text-white h-8 w-8 drop-shadow-md" />
                            </div>
                        </div>
                    </DialogTrigger>
                ) : (
                    // Show placeholder if completed but no image (shouldn't happen) or just fallback
                     !isProcessing && !isFailed && <div className="h-full w-full bg-gray-200 flex items-center justify-center text-gray-400 text-xs">No Image Data</div>
                )}
            </div>
            
            <div className="p-3">
                <div className="mb-2 flex items-center justify-between">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${
                        isCompleted ? 'bg-green-50 text-green-700 ring-green-600/20' :
                        isFailed ? 'bg-red-50 text-red-700 ring-red-600/20' :
                        'bg-blue-50 text-blue-700 ring-blue-600/20'
                    }`}>
                        {generation.status}
                    </span>
                    <span className="text-[10px] text-gray-400">
                        {new Date(generation.created_at).toLocaleDateString()}
                    </span>
                </div>
                <p className="line-clamp-2 text-xs text-gray-600" title={generation.custom_prompt_override || generation.prompt}>
                    {generation.custom_prompt_override || generation.prompt}
                </p>
                {isFailed && generation.error_message && (
                    <p className="mt-2 text-[10px] text-red-600 line-clamp-1">{generation.error_message}</p>
                )}
            </div>
        </div>
        
        {/* Dialog Content */}
        {imageUrl && (
            <DialogContent className="sm:max-w-3xl">
                <DialogHeader>
                    <DialogTitle>Generated Image</DialogTitle>
                </DialogHeader>
                <div className="flex flex-col gap-4 mt-2">
                    <div className="flex items-center justify-center bg-gray-50 rounded-lg overflow-hidden min-h-[300px] max-h-[60vh]">
                         <img 
                            src={imageUrl} 
                            alt={generation.prompt}
                            className="h-full w-auto object-contain max-h-[60vh]"
                        />
                    </div>
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div className="text-sm text-gray-700">
                             <strong>Prompt:</strong> 
                             <p className="text-gray-500 mt-1 max-h-20 overflow-y-auto">
                                {generation.custom_prompt_override || generation.prompt}
                             </p>
                        </div>
                        <Button onClick={handleDownload} className="shrink-0">
                            <Download className="mr-2 h-4 w-4" />
                            Download
                        </Button>
                    </div>
                </div>
            </DialogContent>
        )}
        </Dialog>
    );
}
