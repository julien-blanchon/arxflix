"use client"

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { FileText, BookOpen, Globe, Zap, Database } from 'lucide-react';

export type ContentType = 'research' | 'tutorial' | 'general';
export type ProcessingMethod = 'arxiv' | 'firecrawl';

interface ContentTypeIndicatorProps {
  contentType: ContentType;
  processingMethod: ProcessingMethod;
  confidenceScore?: number;
  sourceUrl: string;
  className?: string;
}

export function ContentTypeIndicator({
  contentType,
  processingMethod,
  confidenceScore,
  sourceUrl,
  className = ""
}: ContentTypeIndicatorProps) {
  
  const getContentTypeConfig = (type: ContentType) => {
    switch (type) {
      case 'research':
        return {
          label: 'Research Paper',
          icon: FileText,
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          description: 'Academic research content with specialized formatting'
        };
      case 'tutorial':
        return {
          label: 'Tutorial Content',
          icon: BookOpen,
          color: 'bg-green-100 text-green-800 border-green-200',
          description: 'Instructional content with step-by-step guidance'
        };
      case 'general':
        return {
          label: 'General Content',
          icon: Globe,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          description: 'General web content with key points focus'
        };
      default:
        return {
          label: 'Unknown',
          icon: Globe,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          description: 'Content type not determined'
        };
    }
  };

  const getProcessingMethodConfig = (method: ProcessingMethod) => {
    switch (method) {
      case 'arxiv':
        return {
          label: 'arXiv Processing',
          icon: Zap,
          color: 'bg-purple-100 text-purple-800 border-purple-200',
          description: 'Optimized processing for academic papers'
        };
      case 'firecrawl':
        return {
          label: 'Web Scraping',
          icon: Database,
          color: 'bg-orange-100 text-orange-800 border-orange-200',
          description: 'General web content extraction'
        };
      default:
        return {
          label: 'Unknown Method',
          icon: Database,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          description: 'Processing method not specified'
        };
    }
  };

  const contentConfig = getContentTypeConfig(contentType);
  const processingConfig = getProcessingMethodConfig(processingMethod);
  
  const ContentIcon = contentConfig.icon;
  const ProcessingIcon = processingConfig.icon;

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname + (urlObj.pathname !== '/' ? urlObj.pathname : '');
    } catch {
      return url;
    }
  };

  return (
    <div className={`space-y-3 p-4 bg-white border rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">Content Analysis</h3>
        {confidenceScore !== undefined && (
          <span className="text-xs text-gray-500">
            Confidence: {Math.round(confidenceScore * 100)}%
          </span>
        )}
      </div>

      {/* Content Type */}
      <div className="flex items-center space-x-3">
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${contentConfig.color}`}>
          <ContentIcon className="h-4 w-4" />
          <span className="text-sm font-medium">{contentConfig.label}</span>
        </div>
        <span className="text-xs text-gray-600">{contentConfig.description}</span>
      </div>

      {/* Processing Method */}
      <div className="flex items-center space-x-3">
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${processingConfig.color}`}>
          <ProcessingIcon className="h-4 w-4" />
          <span className="text-sm font-medium">{processingConfig.label}</span>
        </div>
        <span className="text-xs text-gray-600">{processingConfig.description}</span>
      </div>

      {/* Source URL */}
      <div className="pt-2 border-t border-gray-100">
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">Source:</span>
          <a 
            href={sourceUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:text-blue-800 underline truncate max-w-xs"
            title={sourceUrl}
          >
            {formatUrl(sourceUrl)}
          </a>
        </div>
      </div>
    </div>
  );
}

