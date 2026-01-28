import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { GenerationRequest, GeneratedImage, CreateGenerationPayload } from '@/lib/types';

export function useGeneration(productId?: number) {
  const [generations, setGenerations] = useState<GenerationRequest[]>([]);
  const [gallery, setGallery] = useState<GeneratedImage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Fetch history
  const fetchHistory = useCallback(async () => {
    if (!productId) return;
    setIsLoadingHistory(true);
    try {
      const response = await api.get<GenerationRequest[]>(`/products/${productId}/generations?limit=20`);
      setGenerations(response.data);
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [productId]);

  // Create new generation
  const generate = async (payload: CreateGenerationPayload) => {
    if (!productId) return;
    setIsGenerating(true);
    try {
      const response = await api.post<GenerationRequest>(`/products/${productId}/generate`, payload);
      const newGen = response.data;
      
      // Optimistically add to list
      setGenerations(prev => [newGen, ...prev]);
      
      // Start polling for this specific generation
      pollStatus(newGen.id);
      
      return newGen;
    } catch (e) {
      console.error("Generation failed", e);
      throw e;
    } finally {
      setIsGenerating(false);
    }
  };

  // Simple polling mechanism
  const pollStatus = async (id: number) => {
    const interval = setInterval(async () => {
      try {
        const res = await api.get<GenerationRequest>(`/generation-requests/${id}`);
        const updated = res.data;
        
        setGenerations(prev => prev.map(g => g.id === id ? updated : g));

        if (updated.status === 'completed' || updated.status === 'failed') {
          clearInterval(interval);
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 2000); // Poll every 2s

    // Stop polling after 60s timeout just in case
    setTimeout(() => clearInterval(interval), 60000);
  };

  return {
    generations,
    isGenerating,
    isLoadingHistory,
    fetchHistory,
    generate
  };
}
