import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { UploadState } from '@/types/email.types';

// Extend Window interface for PDF.js
declare global {
  interface Window {
    pdfjsLib?: any;
  }
}

interface EmailUploadProps {
  onFileContent: (content: string, filename: string) => void;
  uploadState: UploadState;
}

export function EmailUpload({ onFileContent, uploadState }: EmailUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load PDF.js dynamically from CDN
  const loadPDFJS = async () => {
    if (window.pdfjsLib) return window.pdfjsLib;
    
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs';
      script.type = 'module';
      
      script.onload = () => {
        // Wait a bit for the library to initialize
        setTimeout(() => {
          if (window.pdfjsLib) {
            window.pdfjsLib.GlobalWorkerOptions.workerSrc = 
              'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';
            resolve(window.pdfjsLib);
          } else {
            reject(new Error('Failed to load PDF.js'));
          }
        }, 100);
      };
      
      script.onerror = () => reject(new Error('Failed to load PDF.js script'));
      document.head.appendChild(script);
    });
  };

  const extractTextFromPDF = async (file: File): Promise<string> => {
    const pdfjsLib = await loadPDFJS();
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    
    let fullText = '';
    
    // Extract text from each page
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item: any) => item.str)
        .join(' ');
      fullText += pageText + '\n';
    }
    
    return fullText.trim();
  };

  const processFile = useCallback(async (file: File) => {
    setSelectedFile(file);
    
    try {
      if (file.name.toLowerCase().endsWith('.pdf')) {

        const text = await extractTextFromPDF(file);
        onFileContent(text, file.name);
      } else {

        const text = await file.text();
        onFileContent(text, file.name);
      }
    } catch (error) {
      console.error('Error processing file:', error);
      throw error;
    }
  }, [onFileContent]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      processFile(file);
    }
  }, [processFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    multiple: false,
  });

  const clearFile = () => {
    setSelectedFile(null);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Upload de Arquivo
        </CardTitle>
        <CardDescription>
          Envie um arquivo .txt ou .pdf contendo o email para análise
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
            isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50",
            uploadState.isUploading && "pointer-events-none opacity-50"
          )}
        >
          <input {...getInputProps()} />
          <div className="space-y-4">
            <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
            {isDragActive ? (
              <p className="text-primary font-medium">Solte o arquivo aqui...</p>
            ) : (
              <div className="space-y-2">
                <p className="font-medium">Clique para selecionar ou arraste um arquivo</p>
                <p className="text-sm text-muted-foreground">
                  Formatos suportados: .txt, .pdf (máx. 10MB)
                </p>
              </div>
            )}
          </div>
        </div>

        {uploadState.isUploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Processando arquivo...</span>
              <span>{uploadState.progress}%</span>
            </div>
            <Progress value={uploadState.progress} />
          </div>
        )}

        {selectedFile && !uploadState.isUploading && (
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              <File className="h-4 w-4" />
              <span className="text-sm font-medium">{selectedFile.name}</span>
              <Badge variant="secondary" className="text-xs">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFile}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {uploadState.error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{uploadState.error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}