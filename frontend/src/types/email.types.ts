export interface Email {
  id: string;
  content: string;
  subject?: string;
  sender?: string;
  timestamp: Date;
}

export interface StructuredResponse {
  to: string;
  subject: string;
  body: string;
}

export interface EmailClassification {
  id: string;
  email: Email;
  category: 'productive' | 'unproductive';
  confidence?: number;
  reasoning: string;
  suggestedResponse: StructuredResponse;
  processedAt: Date;
}

export interface ProcessingState {
  isProcessing: boolean;
  error: string | null;
  result: EmailClassification | null;
}

export interface UploadState {
  isUploading: boolean;
  progress: number;
  error: string | null;
}