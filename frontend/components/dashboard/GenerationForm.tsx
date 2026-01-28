import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Sparkles } from 'lucide-react';

interface GenerationFormProps {
  onGenerate: (prompt: string, aspectRatio: string) => Promise<void>;
  isGenerating: boolean;
  disabled?: boolean;
}

export function GenerationForm({ onGenerate, isGenerating, disabled }: GenerationFormProps) {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    await onGenerate(prompt, aspectRatio);
    // keeping prompt for easy iteration? or clear it? 
    // Usually keeping it is better for refinement.
  };

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-900 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-purple-500" />
        New Generation
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Custom Prompt Additions</label>
            <textarea
                className="w-full rounded-md border border-gray-200 p-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 min-h-[100px]"
                placeholder="e.g. Studio lighting, cinematic angle, marble background..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={disabled || isGenerating}
            />
        </div>

        <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Aspect Ratio</label>
            <div className="flex gap-2">
                {['1:1', '16:9', '9:16', '4:3'].map(ratio => (
                    <button
                        key={ratio}
                        type="button"
                        onClick={() => setAspectRatio(ratio)}
                        disabled={disabled || isGenerating}
                        className={`rounded px-3 py-1.5 text-xs font-medium border transition-colors ${
                            aspectRatio === ratio
                                ? 'bg-blue-100 text-blue-700 border-blue-200'
                                : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                        }`}
                    >
                        {ratio}
                    </button>
                ))}
            </div>
        </div>

        <Button 
            type="submit" 
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0"
            disabled={disabled || isGenerating || !prompt.trim()}
        >
            {isGenerating ? (
                <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                </>
            ) : (
                <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Image
                </>
            )}
        </Button>
      </form>
    </div>
  );
}
