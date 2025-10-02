import React from 'react';
import { Mail, Sparkles } from 'lucide-react';

export function Header() {
  return (
    <header className="border-b bg-card shadow-sm">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          
          <div className="flex items-center gap-2.5">
            <Mail className="h-5 w-5 text-primary" />
            <h1 className="text-lg font-medium text-foreground">
              AutoUMail
            </h1>
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-purple-500" />
            <span className="text-xs font-semibold bg-gradient-to-r from-purple-500 to-blue-500 bg-clip-text text-transparent">
              Powered by AI
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
