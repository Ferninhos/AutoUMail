import React from 'react';
import { History, Search, Filter, Trash2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import type { EmailClassification } from '@/types/email.types';

interface EmailHistoryProps {
  history: EmailClassification[];
  onSelect?: (item: EmailClassification) => void;
  onClear?: () => void;
}

export function EmailHistory({ history, onSelect, onClear }: EmailHistoryProps) {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [filterCategory, setFilterCategory] = React.useState<'all' | 'productive' | 'unproductive'>('all');

  const filteredHistory = React.useMemo(() => {
    return history.filter(item => {
      const matchesSearch = searchTerm === '' || 
        item.email.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.email.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        '';
      
      const matchesFilter = filterCategory === 'all' || item.category === filterCategory;
      
      return matchesSearch && matchesFilter;
    });
  }, [history, searchTerm, filterCategory]);

  const productiveCount = history.filter(item => item.category === 'productive').length;
  const unproductiveCount = history.filter(item => item.category === 'unproductive').length;

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4" />
          Histórico de Análises
        </CardTitle>
        <CardDescription>
          {history.length} emails processados
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Search and Filter */}
        <div className="space-y-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar emails..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          
          <div className="flex gap-1">
            <Button
              variant={filterCategory === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterCategory('all')}
              className="h-7 text-xs"
            >
              Todos ({history.length})
            </Button>
            <Button
              variant={filterCategory === 'productive' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterCategory('productive')}
              className="h-7 text-xs"
            >
              Produtivos ({productiveCount})
            </Button>
            <Button
              variant={filterCategory === 'unproductive' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterCategory('unproductive')}
              className="h-7 text-xs"
            >
              Improdutivos ({unproductiveCount})
            </Button>
          </div>
        </div>

        <Separator />

        {/* History List */}
        <ScrollArea className="h-[400px]">
          <div className="space-y-2">
            {filteredHistory.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  {history.length === 0 ? 'Nenhum email processado ainda' : 'Nenhum resultado encontrado'}
                </p>
              </div>
            ) : (
              filteredHistory.map((item, index) => (
                <div
                  key={item.id}
                  className="p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => onSelect?.(item)}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge 
                      variant={item.category === 'productive' ? 'default' : 'secondary'}
                      className={`text-xs ${
                        item.category === 'productive' 
                          ? 'bg-productive text-productive-foreground' 
                          : 'bg-unproductive text-unproductive-foreground'
                      }`}
                    >
                      {item.category === 'productive' ? 'Produtivo' : 'Improdutivo'}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {Math.round(item.confidence * 100)}%
                    </span>
                  </div>
                  
                  <p className="text-sm line-clamp-2 mb-1">
                    {item.email.content.substring(0, 100)}...
                  </p>
                  
                  <div className="text-xs text-muted-foreground">
                    {item.processedAt.toLocaleString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {history.length > 0 && (
          <>
            <Separator />
            <Button
              variant="outline"
              size="sm"
              onClick={onClear}
              className="w-full h-8 text-xs"
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Limpar Histórico
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}