import { useState, useEffect } from 'react';
import { X, Save, Loader2, RotateCcw, Check } from 'lucide-react';
import { Specification } from '@/lib/types';
import { 
  getSpecifications, 
  getSpecification,
  createSpecification, 
  activateSpecification 
} from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface SpecificationEditorProps {
  isOpen: boolean;
  onClose: () => void;
  productId: number;
  productSlug: string;
  onSaveSuccess: () => void;
}

export function SpecificationEditor({
  isOpen,
  onClose,
  productId,
  productSlug,
  onSaveSuccess,
}: SpecificationEditorProps) {
  const [activeTab, setActiveTab] = useState<'edit' | 'history'>('edit');
  const [yamlContent, setYamlContent] = useState('');
  const [changeNotes, setChangeNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [versions, setVersions] = useState<Specification[]>([]);
  const { toast } = useToast();

  // Load active specification when modal opens
  useEffect(() => {
    if (isOpen) {
      loadActiveSpecification();
      setActiveTab('edit');
      setChangeNotes('');
      setError(null);
    }
  }, [isOpen, productId]);

  // Load version history when switching to history tab
  useEffect(() => {
    if (isOpen && activeTab === 'history') {
      loadVersionHistory();
    }
  }, [isOpen, activeTab, productId]);

  const loadActiveSpecification = async () => {
    setIsLoading(true);
    try {
      const response = await getSpecifications(productId);
      const activeSpec = response.data.find((s: Specification) => s.is_active);
      
      if (activeSpec) {
        // Load full YAML content
        const fullSpec = await getSpecification(productId, activeSpec.id);
        setYamlContent(fullSpec.data.yaml_content);
      } else {
        setYamlContent('# No active specification found\n# Create your first specification here\n');
      }
    } catch (err) {
      console.error('Failed to load specification', err);
      setError('Failed to load specification');
      toast({
        title: 'Error',
        description: 'Failed to load specification',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadVersionHistory = async () => {
    setIsLoading(true);
    try {
      const response = await getSpecifications(productId);
      setVersions(response.data);
    } catch (err) {
      console.error('Failed to load version history', err);
      setError('Failed to load version history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!yamlContent.trim()) {
      setError('YAML content cannot be empty');
      return;
    }

    setIsSaving(true);
    setError(null);
    
    try {
      await createSpecification(productId, {
        yaml_content: yamlContent,
        change_notes: changeNotes || undefined,
      });

      toast({
        title: 'Saved',
        description: 'Specification saved as new version',
      });

      onSaveSuccess();
      onClose();
    } catch (err: unknown) {
      console.error('Failed to save specification', err);
      const errorMsg = (err && typeof err === 'object' && 'response' in err && err.response && typeof err.response === 'object' && 'data' in err.response && err.response.data && typeof err.response.data === 'object' && 'detail' in err.response.data) ? String(err.response.data.detail) : 'Failed to save specification';
      setError(errorMsg);
      toast({
        title: 'Error',
        description: errorMsg,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRevert = async (specId: number) => {
    if (!confirm('Are you sure you want to revert to this version? This will become the new active version.')) {
      return;
    }

    setIsSaving(true);
    try {
      await activateSpecification(productId, specId);
      
      toast({
        title: 'Reverted',
        description: 'Specification version activated',
      });

      onSaveSuccess();
      
      // Refresh history and reload active spec
      await loadVersionHistory();
      await loadActiveSpecification();
      setActiveTab('edit');
    } catch (err: unknown) {
      console.error('Failed to revert version', err);
      const errorMsg = (err && typeof err === 'object' && 'response' in err && err.response && typeof err.response === 'object' && 'data' in err.response && err.response.data && typeof err.response.data === 'object' && 'detail' in err.response.data) ? String(err.response.data.detail) : 'Failed to revert version';
      setError(errorMsg);
      toast({
        title: 'Error',
        description: errorMsg,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="flex h-[80vh] w-[800px] flex-col overflow-hidden rounded-lg bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Specification Manager
            </h2>
            <div className="flex rounded-lg bg-gray-100 p-1">
              <button
                onClick={() => setActiveTab('edit')}
                className={`rounded-md px-3 py-1 text-sm font-medium transition-all ${
                  activeTab === 'edit'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Editor
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`rounded-md px-3 py-1 text-sm font-medium transition-all ${
                  activeTab === 'history'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                History
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 hover:bg-gray-100"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="border-b border-red-100 bg-red-50 px-6 py-2 text-xs text-red-600">
            {error}
          </div>
        )}

        {/* Content Area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {activeTab === 'edit' ? (
            <div className="flex flex-1 flex-col p-6">
              {isLoading ? (
                <div className="flex h-full items-center justify-center text-gray-500">
                  <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                  Loading...
                </div>
              ) : (
                <>
                  <textarea
                    className="h-full w-full resize-none rounded-md border border-gray-300 p-4 font-mono text-sm focus:border-purple-500 focus:outline-none"
                    value={yamlContent}
                    onChange={(e) => setYamlContent(e.target.value)}
                    placeholder="Enter YAML content..."
                  />
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Change Notes (Optional)
                    </label>
                    <input
                      type="text"
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
                      value={changeNotes}
                      onChange={(e) => setChangeNotes(e.target.value)}
                      placeholder="Describe what changed in this version..."
                    />
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6">
              {isLoading ? (
                <div className="flex h-full items-center justify-center text-gray-500">
                  <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                  Loading history...
                </div>
              ) : (
                <div className="space-y-4">
                  {versions.map((version) => (
                    <div
                      key={version.id}
                      className={`flex items-center justify-between rounded-lg border p-4 ${
                        version.is_active
                          ? 'border-purple-200 bg-purple-50'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">
                            Version {version.version}
                          </span>
                          {version.is_active && (
                            <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
                              Active
                            </span>
                          )}
                        </div>
                        {version.change_notes && (
                          <div className="mt-1 text-sm text-gray-600">
                            {version.change_notes}
                          </div>
                        )}
                        <div className="mt-1 text-xs text-gray-500">
                          Created: {new Date(version.created_at).toLocaleString()}
                        </div>
                      </div>

                      {!version.is_active && (
                        <button
                          onClick={() => handleRevert(version.id)}
                          disabled={isSaving}
                          className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Revert
                        </button>
                      )}
                      {version.is_active && (
                        <div className="flex items-center gap-1 text-xs font-medium text-purple-700">
                          <Check className="h-3 w-3" />
                          Current
                        </div>
                      )}
                    </div>
                  ))}
                  {versions.length === 0 && (
                    <p className="text-center text-gray-500">
                      No version history found.
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t bg-gray-50 px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
            disabled={isSaving}
          >
            Close
          </button>
          {activeTab === 'edit' && (
            <button
              onClick={handleSave}
              disabled={isSaving || isLoading}
              className="flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save as New Version
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
