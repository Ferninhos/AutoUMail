import React from 'react';
import { Button } from '@/components/ui/button';
import { Download, FileText, File } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { EmailClassification } from '@/types/email.types';
import { jsPDF } from 'jspdf';
import { saveAs } from 'file-saver';

interface DownloadActionsProps {
  result: EmailClassification;
}

export function DownloadActions({ result }: DownloadActionsProps) {
  const { toast } = useToast();

  const formatAnalysisText = (): string => {
    const date = new Date(result.processedAt).toLocaleString('pt-BR');
    const confidence = result.confidence 
      ? `${Math.round(result.confidence * 100)}%` 
      : 'N/A';

    return `ANÁLISE DE EMAIL
================
Categoria: ${result.category === 'productive' ? 'Produtivo' : 'Improdutivo'}
Confiança: ${confidence}
Data da Análise: ${date}

RESPOSTA SUGERIDA
================
Para: ${result.suggestedResponse.to}
Assunto: ${result.suggestedResponse.subject}

${result.suggestedResponse.body}

ANÁLISE DA IA
=============
${result.reasoning}
`;
  };

  const downloadAsTxt = () => {
    try {
      const content = formatAnalysisText();
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const filename = `email-analise-${Date.now()}.txt`;
      saveAs(blob, filename);
      
      toast({
        title: "Download concluído!",
        description: "Arquivo .txt baixado com sucesso.",
      });
    } catch (error) {
      console.error('Error downloading TXT:', error);
      toast({
        title: "Erro no download",
        description: "Não foi possível gerar o arquivo .txt",
        variant: "destructive",
      });
    }
  };

  const downloadAsPdf = () => {
    try {
      const doc = new jsPDF();
      const date = new Date(result.processedAt).toLocaleString('pt-BR');
      const confidence = result.confidence 
        ? `${Math.round(result.confidence * 100)}%` 
        : 'N/A';
      
      // Title
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('ANÁLISE DE EMAIL', 20, 20);
      
      // Separator
      doc.setLineWidth(0.5);
      doc.line(20, 25, 190, 25);
      
      // Classification Info
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text('Categoria:', 20, 35);
      doc.setFont('helvetica', 'normal');
      doc.text(result.category === 'productive' ? 'Produtivo' : 'Improdutivo', 50, 35);
      
      doc.setFont('helvetica', 'bold');
      doc.text('Confiança:', 20, 42);
      doc.setFont('helvetica', 'normal');
      doc.text(confidence, 50, 42);
      
      doc.setFont('helvetica', 'bold');
      doc.text('Data da Análise:', 20, 49);
      doc.setFont('helvetica', 'normal');
      doc.text(date, 50, 49);
      
      // Suggested Response Section
      let yPos = 60;
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('RESPOSTA SUGERIDA', 20, yPos);
      doc.line(20, yPos + 2, 190, yPos + 2);
      
      yPos += 10;
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text('Para:', 20, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(result.suggestedResponse.to, 35, yPos);
      
      yPos += 7;
      doc.setFont('helvetica', 'bold');
      doc.text('Assunto:', 20, yPos);
      doc.setFont('helvetica', 'normal');
      const subjectLines = doc.splitTextToSize(result.suggestedResponse.subject, 150);
      doc.text(subjectLines, 35, yPos);
      yPos += subjectLines.length * 5 + 5;
      
      // Email Body
      doc.setFont('helvetica', 'normal');
      const bodyLines = doc.splitTextToSize(result.suggestedResponse.body, 170);
      doc.text(bodyLines, 20, yPos);
      yPos += bodyLines.length * 5 + 10;
      
      // Check if we need a new page
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }
      
      // AI Analysis Section
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('ANÁLISE DA IA', 20, yPos);
      doc.line(20, yPos + 2, 190, yPos + 2);
      
      yPos += 10;
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      const reasoningLines = doc.splitTextToSize(result.reasoning, 170);
      doc.text(reasoningLines, 20, yPos);
      
      // Save PDF
      const filename = `email-analise-${Date.now()}.pdf`;
      doc.save(filename);
      
      toast({
        title: "Download concluído!",
        description: "Arquivo .pdf baixado com sucesso.",
      });
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast({
        title: "Erro no download",
        description: "Não foi possível gerar o arquivo .pdf",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        onClick={downloadAsTxt}
        size="sm"
        variant="outline"
        className="h-7 text-xs"
      >
        <FileText className="h-3 w-3 mr-1" />
        Download .txt
      </Button>
      <Button
        onClick={downloadAsPdf}
        size="sm"
        variant="outline"
        className="h-7 text-xs"
      >
        <File className="h-3 w-3 mr-1" />
        Download .pdf
      </Button>
    </div>
  );
}
