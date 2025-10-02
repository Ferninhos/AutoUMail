import React from 'react';
import { CheckCircle, AlertCircle, Copy, RotateCcw, Sparkles, Mail, Brain, Info } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { DownloadActions } from './DownloadActions';
import type { EmailClassification } from '@/types/email.types';

interface EmailResultsProps {
  result: EmailClassification;
  onReclassify?: (id: string, newCategory: 'productive' | 'unproductive') => void;
}

export function EmailResults({ result, onReclassify }: EmailResultsProps) {
  const { toast } = useToast();

  const copyEmailBody = async () => {
    try {
      await navigator.clipboard.writeText(result.suggestedResponse.body);
      toast({
        title: "Corpo copiado!",
        description: "O corpo da resposta foi copiado para a área de transferência.",
      });
    } catch (error) {
      toast({
        title: "Erro ao copiar",
        description: "Não foi possível copiar a resposta.",
        variant: "destructive",
      });
    }
  };

  const copyFullEmail = async () => {
    try {
      const fullEmail = `Para: ${result.suggestedResponse.to}
Assunto: ${result.suggestedResponse.subject}

${result.suggestedResponse.body}`;
      
      await navigator.clipboard.writeText(fullEmail);
      toast({
        title: "Email completo copiado!",
        description: "O email completo foi copiado para a área de transferência.",
      });
    } catch (error) {
      toast({
        title: "Erro ao copiar",
        description: "Não foi possível copiar o email.",
        variant: "destructive",
      });
    }
  };

  const handleReclassify = (newCategory: 'productive' | 'unproductive') => {
    if (onReclassify) {
      onReclassify(result.id, newCategory);
      toast({
        title: "Reclassificação enviada",
        description: "Obrigado pelo feedback! Isso nos ajuda a melhorar.",
      });
    }
  };

  const isProductive = result.category === 'productive';

  return (
    <div className="space-y-6">

      <div className="grid grid-cols-2 gap-4">

        <Card className="border shadow-none">
          <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4 min-h-[200px]">
            {isProductive ? (
              <CheckCircle className="h-12 w-12 text-productive" />
            ) : (
              <AlertCircle className="h-12 w-12 text-unproductive" />
            )}
            
            <div className="space-y-2">
              <Badge 
                variant={isProductive ? "default" : "secondary"}
                className={isProductive 
                  ? "bg-productive text-productive-foreground border-0 text-sm px-3 py-1" 
                  : "bg-unproductive text-unproductive-foreground border-0 text-sm px-3 py-1"
                }
              >
                {isProductive ? "Produtivo" : "Improdutivo"}
              </Badge>
              
              <p className="text-xs text-muted-foreground leading-relaxed">
                {isProductive 
                  ? "Requer ação ou resposta" 
                  : "Não requer ação imediata"
                }
              </p>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleReclassify(isProductive ? 'unproductive' : 'productive')}
              className="h-7 text-xs"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reclassificar
            </Button>
          </CardContent>
        </Card>

        <Card className="border shadow-none bg-blue-50 dark:bg-blue-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-1.5 text-blue-900 dark:text-blue-100">
              <Brain className="h-4 w-4" />
              Análise da IA
            </CardTitle>
          </CardHeader>
          <CardContent className="min-h-[148px] flex items-start">
            <p className="text-xs leading-relaxed text-blue-800 dark:text-blue-200">
              {result.reasoning}
            </p>
          </CardContent>
        </Card>
      </div>


      <Card className="border shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            Resposta Sugerida
          </CardTitle>
          <CardDescription className="text-xs">
            Email {isProductive ? 'completo' : 'simples'} gerado pela IA
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">

          <div className="space-y-1.5 pb-2 border-b">
            <div className="flex items-start gap-2">
              <span className="text-xs font-medium text-muted-foreground min-w-[50px]">Para:</span>
              <span className="text-xs">{result.suggestedResponse.to}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-xs font-medium text-muted-foreground min-w-[50px]">Assunto:</span>
              <span className="text-xs">{result.suggestedResponse.subject}</span>
            </div>
          </div>

          <div className="bg-muted/40 p-3 rounded border">
            <p className="text-xs leading-relaxed whitespace-pre-line">
              {result.suggestedResponse.body}
            </p>
          </div>
          
          <div className="flex justify-between items-center gap-2 pt-1">
            <div className="flex gap-2">
              <Button 
                onClick={copyEmailBody} 
                size="sm" 
                variant="ghost" 
                className="h-7 text-xs"
              >
                <Copy className="h-3 w-3 mr-1" />
                Copiar Corpo
              </Button>
              <Button 
                onClick={copyFullEmail} 
                size="sm" 
                className="h-7 text-xs"
              >
                <Mail className="h-3 w-3 mr-1" />
                Email Completo
              </Button>
            </div>
            
            <DownloadActions result={result} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}