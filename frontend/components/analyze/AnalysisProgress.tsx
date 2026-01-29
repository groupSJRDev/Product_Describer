import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

interface AnalysisProgressProps {
  status: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';
  progress?: number;
  message?: string;
}

export function AnalysisProgress({ status, progress = 0, message }: AnalysisProgressProps) {
  if (status === 'idle') return null;

  return (
    <div className="rounded-lg border bg-white p-6">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="flex-shrink-0">
          {status === 'uploading' && (
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          )}
          {status === 'analyzing' && (
            <Loader2 className="h-8 w-8 text-purple-600 animate-spin" />
          )}
          {status === 'complete' && (
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          )}
          {status === 'error' && (
            <AlertCircle className="h-8 w-8 text-red-600" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          <div>
            <h3 className="font-semibold text-gray-900">
              {status === 'uploading' && 'Uploading Images...'}
              {status === 'analyzing' && 'Analyzing Product...'}
              {status === 'complete' && 'Analysis Complete!'}
              {status === 'error' && 'Analysis Failed'}
            </h3>
            {message && (
              <p className="text-sm text-gray-600 mt-1">{message}</p>
            )}
          </div>

          {/* Progress Bar */}
          {(status === 'uploading' || status === 'analyzing') && (
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  status === 'uploading' ? 'bg-blue-600' : 'bg-purple-600'
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          )}

          {/* Status Details */}
          <div className="text-xs text-gray-500">
            {status === 'uploading' && 'Uploading images to server...'}
            {status === 'analyzing' && 'GPT Vision is analyzing your product images...'}
            {status === 'complete' && 'Specification has been generated successfully'}
            {status === 'error' && 'An error occurred during analysis. Please try again.'}
          </div>
        </div>
      </div>
    </div>
  );
}
