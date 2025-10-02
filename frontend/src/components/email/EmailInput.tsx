import React from 'react';
import { MessageSquare } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface EmailInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  currentCategory?: 'productive' | 'unproductive';
}

export function EmailInput({ 
  value, 
  onChange, 
  placeholder = "Cole o conteúdo do email aqui...",
  disabled = false,
  currentCategory
}: EmailInputProps) {
  return (
    <Card className="w-full border shadow-none">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            <CardTitle className="text-base font-medium">Entrada de Texto</CardTitle>
          </div>
          {currentCategory && value.length > 0 && (
            <div className="flex items-center gap-2">
              {currentCategory === 'productive' ? (
                <>
                  <div className="h-2 w-2 rounded-full bg-productive animate-pulse" />
                  <span className="text-xs font-medium text-productive">Produtivo</span>
                </>
              ) : (
                <>
                  <div className="h-2 w-2 rounded-full bg-unproductive animate-pulse" />
                  <span className="text-xs font-medium text-unproductive">Improdutivo</span>
                </>
              )}
            </div>
          )}
        </div>
        <CardDescription className="text-xs">
          Cole diretamente o conteúdo do email para análise
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="email-content" className="text-sm font-normal">Conteúdo do Email</Label>
          <Textarea
            id="email-content"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            className="min-h-[200px] resize-y border focus-visible:ring-1"
            aria-describedby="email-content-help"
          />
          <p id="email-content-help" className="text-xs text-muted-foreground">
            {value.length > 0 ? `${value.length} caracteres` : 'Digite ou cole o email completo aqui'}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}