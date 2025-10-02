import React, { useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { EmailUpload } from '@/components/email/EmailUpload';
import { EmailInput } from '@/components/email/EmailInput';
import { EmailResults } from '@/components/email/EmailResults';
import { EmailHistory } from '@/components/email/EmailHistory';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Zap, FileText, MessageSquare, Brain, Sparkles, Copy, Mail, CheckCircle, AlertCircle, RotateCcw, Building2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { Email, EmailClassification, ProcessingState, UploadState } from '@/types/email.types';
import { parseEmailContent } from '@/utils/emailParser';
import { useEmailHistory } from '@/hooks/useEmailHistory';
import { useCompanyProfile } from '@/hooks/useCompanyProfile';
import { CompanyProfileDialog } from '@/components/dashboard/CompanyProfileDialog';


const classifyEmail = async (
  emailContent: string, 
  subject?: string, 
  sender?: string,
  companyProfile?: any
): Promise<EmailClassification> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  try {
    const apiUrl = `${process.env.NODE_ENV === 'production' ? 'https://first-project-code.onrender.com' : 'http://localhost:8000'}/classify-email`;
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: emailContent,
        subject: subject || undefined,
        sender: sender || undefined,
        config_id: companyProfile?.config_id || undefined
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    return result;
    
  } catch (error) {
    clearTimeout(timeoutId);
    

    const isProductive = emailContent.toLowerCase().includes('problema') || 
                        emailContent.toLowerCase().includes('dúvida') ||
                        emailContent.toLowerCase().includes('solicitação') ||
                        emailContent.toLowerCase().includes('urgente') ||
                        emailContent.toLowerCase().includes('help') ||
                        emailContent.toLowerCase().includes('suporte');

    const category = isProductive ? 'productive' : 'unproductive';
    const confidence = 0.3; 
    
    const suggestedResponse = isProductive 
      ? `Prezado(a),\n\nRecebemos sua mensagem e nossa equipe irá analisá-la. Retornaremos o contato em breve.\n\nAtenciosamente,\nEquipe de Suporte`
      : `Prezado(a),\n\nObrigado pela sua mensagem. Recebemos seu contato.\n\nContinuamos à disposição.\n\nAtenciosamente,\nEquipe`;

    return {
      id: `classification-${Date.now()}`,
      email: {
        id: `email-${Date.now()}`,
        content: emailContent,
        timestamp: new Date()
      },
      category,
      confidence,
      suggestedResponse,
      processedAt: new Date()
    };
  }
};

export default function Dashboard() {
  const [emailContent, setEmailContent] = useState('');
  const [activeTab, setActiveTab] = useState('text');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [processingState, setProcessingState] = useState<ProcessingState>({
    isProcessing: false,
    error: null,
    result: null,
  });
  const [uploadState, setUploadState] = useState<UploadState>({
    isUploading: false,
    progress: 0,
    error: null,
  });
  
  const { toast } = useToast();
  const { history, addToHistory, clearHistory: clearHistoryStorage, updateHistoryItem } = useEmailHistory();
  const { profile, saveProfile, clearProfile } = useCompanyProfile();

  const handleFileContent = async (content: string, filename: string) => {
    setUploadState({ isUploading: true, progress: 50, error: null });
    
    try {
      setEmailContent(content);
      setActiveTab('text');
      setUploadState({ isUploading: false, progress: 100, error: null });
      
      toast({
        title: "Arquivo carregado!",
        description: `${filename} processado com sucesso${filename.endsWith('.pdf') ? ' (PDF extraído)' : ''}.`,
      });
    } catch (error) {
      setUploadState({ isUploading: false, progress: 0, error: 'Erro ao processar arquivo' });
      toast({
        title: "Erro no upload",
        description: "Não foi possível processar o arquivo.",
        variant: "destructive",
      });
    }
  };

  const processEmail = async () => {
    if (!emailContent.trim()) {
      toast({
        title: "Erro",
        description: "Por favor, insira o conteúdo do email para análise.",
        variant: "destructive",
      });
      return;
    }

    setProcessingState({
      isProcessing: true,
      error: null,
      result: null,
    });

    try {
      // Parse email para extrair informações estruturadas
      const parsedEmail = parseEmailContent(emailContent);
      
      // Passar as informações extraídas para a API
      const result = await classifyEmail(
        parsedEmail.body || emailContent,
        parsedEmail.subject,
        parsedEmail.from,
        profile || undefined
      );
      
      setProcessingState({
        isProcessing: false,
        error: null,
        result,
      });
      addToHistory(result);
      
      toast({
        title: "Email processado!",
        description: `Classificado como ${result.category === 'productive' ? 'Produtivo' : 'Improdutivo'}${result.confidence ? ` com ${Math.round(result.confidence * 100)}% de confiança` : ''}.`,
      });
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        error: 'Erro ao processar email. Tente novamente.',
        result: null,
      });
      toast({
        title: "Erro no processamento",
        description: "Não foi possível processar o email. Tente novamente.",
        variant: "destructive",
      });
    }
  };

  const handleReclassify = (id: string, newCategory: 'productive' | 'unproductive') => {
    updateHistoryItem(id, { category: newCategory });
  };

  const handleSelectHistoryItem = (item: EmailClassification) => {
    setEmailContent(item.email.content);
    setProcessingState({
      isProcessing: false,
      error: null,
      result: item,
    });
  };

  const handleClearHistory = () => {
    clearHistoryStorage();
    toast({
      title: "Histórico limpo",
      description: "Todos os emails processados foram removidos.",
    });
  };

  const resetForm = () => {
    setEmailContent('');
    setProcessingState({
      isProcessing: false,
      error: null,
      result: null,
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-6 py-8">

        <Card className="mb-6 border-primary/20">
          <CardContent className="pt-6 pb-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                {profile ? (
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Building2 className="h-4 w-4 text-primary" />
                      <p className="text-sm font-medium">
                        ✅ Perfil Personalizado: {profile.company_name}
                      </p>
                    </div>
                    {profile.config_id && (
                      <p className="text-xs text-muted-foreground">
                        ID da Configuração: {profile.config_id}
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Usando critérios padrão
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Configure um perfil personalizado para melhor precisão
                    </p>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setDialogOpen(true)}
                >
                  <Building2 className="h-4 w-4 mr-2" />
                  {profile ? 'Editar Perfil' : 'Configurar Empresa'}
                </Button>
                {profile && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      clearProfile();
                      toast({ title: "Perfil removido", description: "Voltando para critérios padrão" });
                    }}
                  >
                    Remover
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <CompanyProfileDialog 
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          currentProfile={profile}
          onSave={saveProfile}
        />

                <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">Entrada de Email</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Cole ou carregue um email para análise com IA
              </p>
            </div>

            {processingState.result && (
              <Card className="w-full border shadow-sm bg-blue-50 dark:bg-blue-950/20">
                <CardHeader className="pb-2 pt-3 px-4">
                  <CardTitle className="text-xs font-medium flex items-center gap-1.5 text-blue-900 dark:text-blue-100">
                    <Brain className="h-3 w-3" />
                    Análise de IA
                  </CardTitle>
                </CardHeader>

                <CardContent className="px-4 pb-3">
                  <p className="text-xs leading-relaxed text-blue-800 dark:text-blue-200 line-clamp-3">
                    {processingState.result.reasoning}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="space-y-4">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Upload
                </TabsTrigger>
                <TabsTrigger value="text" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Texto
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="upload" className="mt-4">
                <EmailUpload 
                  onFileContent={handleFileContent}
                  uploadState={uploadState}
                />
              </TabsContent>
              
              <TabsContent value="text" className="mt-4">
                <EmailInput
                  value={emailContent}
                  onChange={setEmailContent}
                  disabled={processingState.isProcessing}
                  currentCategory={processingState.result?.category}
                />
              </TabsContent>
            </Tabs>

            <div className="flex gap-3">
              <Button 
                onClick={processEmail}
                disabled={!emailContent.trim() || processingState.isProcessing}
                size="lg"
                className="flex-1"
              >
                {processingState.isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Processar Email
                  </>
                )}
              </Button>
              <Button 
                variant="outline" 
                onClick={resetForm}
                disabled={processingState.isProcessing}
              >
                Limpar
              </Button>
            </div>

            {/* Error State */}
            {processingState.error && (
              <Card className="border-destructive/50 bg-destructive/5">
                <CardContent className="pt-6">
                  <p className="text-destructive text-sm">{processingState.error}</p>
                </CardContent>
              </Card>
            )}
          </div>

          <div>
            {processingState.result ? (
              <div className="space-y-4">
                {/* Classification Badge */}
                <Card className="border shadow-sm">
                  <CardContent className="p-4 flex items-center gap-3">
                    {processingState.result.category === 'productive' ? (
                      <>
                        <CheckCircle className="h-8 w-8 text-productive flex-shrink-0" />
                        <div className="flex-1">
                          <Badge className="bg-productive text-productive-foreground border-0 mb-1">
                            Produtivo
                          </Badge>
                          <p className="text-xs text-muted-foreground">Requer ação ou resposta</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-8 w-8 text-unproductive flex-shrink-0" />
                        <div className="flex-1">
                          <Badge className="bg-unproductive text-unproductive-foreground border-0 mb-1">
                            Improdutivo
                          </Badge>
                          <p className="text-xs text-muted-foreground">Não requer ação imediata</p>
                        </div>
                      </>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleReclassify(
                        processingState.result!.id, 
                        processingState.result!.category === 'productive' ? 'unproductive' : 'productive'
                      )}
                      className="h-8 text-xs"
                    >
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Reclassificar
                    </Button>
                  </CardContent>
                </Card>

                <Card className="border shadow-sm">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base font-medium flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        Resposta Sugerida
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Email completo gerado pela IA
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">

                      <div className="space-y-1.5 pb-2 border-b">
                        <div className="flex items-start gap-2">
                          <span className="text-xs font-medium text-muted-foreground min-w-[50px]">Para:</span>
                          <span className="text-xs">{processingState.result.suggestedResponse.to}</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-xs font-medium text-muted-foreground min-w-[50px]">Assunto:</span>
                          <span className="text-xs">{processingState.result.suggestedResponse.subject}</span>
                        </div>
                      </div>

                      <div className="bg-muted/40 p-3 rounded border">
                        <p className="text-xs leading-relaxed whitespace-pre-line">
                          {processingState.result.suggestedResponse.body}
                        </p>
                      </div>
                      
                      <div className="flex justify-end gap-2 pt-1">
                        <Button 
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(processingState.result!.suggestedResponse.body);
                              toast({ title: "Corpo copiado!", description: "O corpo da resposta foi copiado." });
                            } catch (error) {
                              toast({ title: "Erro ao copiar", variant: "destructive" });
                            }
                          }} 
                          size="sm" 
                          variant="ghost" 
                          className="h-7 text-xs"
                        >
                          <Copy className="h-3 w-3 mr-1" />
                          Copiar Corpo
                        </Button>
                        <Button 
                          onClick={async () => {
                            try {
                              const fullEmail = `Para: ${processingState.result!.suggestedResponse.to}\nAssunto: ${processingState.result!.suggestedResponse.subject}\n\n${processingState.result!.suggestedResponse.body}`;
                              await navigator.clipboard.writeText(fullEmail);
                              toast({ title: "Email completo copiado!" });
                            } catch (error) {
                              toast({ title: "Erro ao copiar", variant: "destructive" });
                            }
                          }} 
                          size="sm" 
                          className="h-7 text-xs"
                        >
                          <Mail className="h-3 w-3 mr-1" />
                          Email Completo
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
              </div>
            ) : (
              <Card className="border shadow-sm h-full min-h-[300px]">
                <CardContent className="h-full flex flex-col items-center justify-center text-center p-6">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Brain className="h-12 w-12 opacity-30" />
                    <div>
                      <p className="text-sm font-medium">Aguardando análise</p>
                      <p className="text-xs mt-1">Processe um email para ver os resultados</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        <div>
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Histórico</h2>
            <p className="text-sm text-muted-foreground">
              Cache local persistente dos emails processados
            </p>
          </div>
          <EmailHistory 
            history={history}
            onSelect={handleSelectHistoryItem}
            onClear={handleClearHistory}
          />
        </div>
      </div>
    </div>
  );
}