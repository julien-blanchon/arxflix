"use client"

import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle, Globe, FileText } from 'lucide-react';

export type InputType = 'arxiv_id' | 'url' | 'unknown';

interface SmartInputProps {
  value: string;
  onChange: (value: string) => void;
  onProcess?: () => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function SmartInput({ 
  value, 
  onChange, 
  onProcess, 
  disabled = false, 
  placeholder = "Enter arXiv ID or URL",
  className = ""
}: SmartInputProps) {
  const [inputType, setInputType] = useState<InputType>('unknown');
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [validationMessage, setValidationMessage] = useState<string>('');

  // Detect input type and validate
  useEffect(() => {
    const detectAndValidate = (input: string) => {
      if (!input.trim()) {
        setInputType('unknown');
        setIsValid(null);
        setValidationMessage('');
        return;
      }

      // Check for arXiv ID pattern (e.g., 2404.02905, 1234.5678v1)
      const arxivIdPattern = /^\d{4}\.\d{4,5}(v\d+)?$/;
      if (arxivIdPattern.test(input.trim())) {
        setInputType('arxiv_id');
        setIsValid(true);
        setValidationMessage('Valid arXiv ID detected');
        return;
      }

      // Check for URL pattern
      const urlPattern = /^https?:\/\/.+/;
      if (urlPattern.test(input.trim())) {
        setInputType('url');
        
        // Basic URL validation
        try {
          new URL(input.trim());
          setIsValid(true);
          
          // Check if it's an arXiv URL
          if (input.includes('arxiv.org')) {
            setValidationMessage('arXiv URL detected - will use optimized processing');
          } else {
            setValidationMessage('Valid URL detected');
          }
        } catch {
          setIsValid(false);
          setValidationMessage('Invalid URL format');
        }
        return;
      }

      // If it doesn't match either pattern
      setInputType('unknown');
      setIsValid(false);
      setValidationMessage('Please enter a valid arXiv ID (e.g., 2404.02905) or URL');
    };

    detectAndValidate(value);
  }, [value]);

  const getInputIcon = () => {
    if (inputType === 'arxiv_id') {
      return <FileText className="h-4 w-4 text-blue-500" />;
    } else if (inputType === 'url') {
      return <Globe className="h-4 w-4 text-green-500" />;
    }
    return null;
  };

  const getValidationIcon = () => {
    if (isValid === true) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (isValid === false) {
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
    return null;
  };

  const getValidationColor = () => {
    if (isValid === true) {
      return 'border-green-500 focus:border-green-500';
    } else if (isValid === false) {
      return 'border-red-500 focus:border-red-500';
    }
    return '';
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="relative">
        <Input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={`pr-20 ${getValidationColor()}`}
        />
        
        {/* Icons container */}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
          {getInputIcon()}
          {getValidationIcon()}
        </div>
      </div>
      
      {/* Validation message */}
      {validationMessage && (
        <div className={`text-sm flex items-center space-x-1 ${
          isValid === true ? 'text-green-600' : 
          isValid === false ? 'text-red-600' : 
          'text-gray-600'
        }`}>
          <span>{validationMessage}</span>
        </div>
      )}
      
      {/* Input type indicator */}
      {inputType !== 'unknown' && (
        <div className="text-xs text-gray-500 flex items-center space-x-1">
          <span>Detected:</span>
          <span className={`font-medium ${
            inputType === 'arxiv_id' ? 'text-blue-600' : 'text-green-600'
          }`}>
            {inputType === 'arxiv_id' ? 'arXiv Paper ID' : 'Web URL'}
          </span>
        </div>
      )}
    </div>
  );
}

