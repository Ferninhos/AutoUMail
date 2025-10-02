import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Building2 } from 'lucide-react';
import { CompanyProfile } from '@/hooks/useCompanyProfile';

interface CompanyProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentProfile: CompanyProfile | null;
  onSave: (profile: CompanyProfile) => void;
}

export function CompanyProfileDialog({ open, onOpenChange, currentProfile, onSave }: CompanyProfileDialogProps) {
  const { toast } = useToast();
  const [formData, setFormData] = useState<CompanyProfile>({
    company_name: '',
    custom_instructions: ''
  });

  useEffect(() => {
    if (currentProfile) {
      setFormData(currentProfile);
    } else {
      setFormData({
        company_name: '',
        custom_instructions: ''
      });
    }
  }, [currentProfile, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.company_name.trim()) {
      toast({
        title: "Campo obrigatório",
        description: "Por favor, preencha o nome da empresa.",
        variant: "destructive"
      });
      return;
    }

    try {
      // Chamar backend para criar/atualizar config
      const apiUrl = `${process.env.NODE_ENV === 'production' ? 'https://first-project-code.onrender.com' : 'http://localhost:8000'}/company-config`;
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: formData.company_name,
          custom_instructions: formData.custom_instructions || ''
        })
      });

      if (!response.ok) {
        throw new Error('Erro ao salvar configuração no servidor');
      }

      const result = await response.json();
      
      // Salvar perfil com config_id
      const profileWithId = {
        ...formData,
        config_id: result.config_id
      };
      
      onSave(profileWithId);
      onOpenChange(false);
      toast({
        title: "Perfil salvo!",
        description: `Configuração criada com ID: ${result.config_id}`
      });
    } catch (error) {
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar a configuração no servidor.",
        variant: "destructive"
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Configurar Perfil da Empresa
          </DialogTitle>
          <DialogDescription>
            Configure o nome da empresa e instruções personalizadas para o assistente de IA.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Company Name */}
          <div className="space-y-2">
            <Label htmlFor="company_name">Nome da Empresa *</Label>
            <Input
              id="company_name"
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              placeholder="Ex: Tech Solutions Ltda"
              required
            />
          </div>

          {/* Custom Instructions */}
          <div className="space-y-2">
            <Label htmlFor="custom_instructions">Particularidades / Instruções Personalizadas</Label>
            <Textarea
              id="custom_instructions"
              value={formData.custom_instructions}
              onChange={(e) => setFormData({ ...formData, custom_instructions: e.target.value })}
              placeholder="Ex: Sempre assine com o nome da empresa no final das respostas. Use tom formal e cordial..."
              className="min-h-[120px]"
            />
            <p className="text-xs text-muted-foreground">
              Instruções específicas para o assistente de IA ao gerar respostas para sua empresa.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" className="flex-1">
              Salvar Perfil
            </Button>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
