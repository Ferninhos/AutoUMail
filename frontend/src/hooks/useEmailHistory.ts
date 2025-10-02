import { useState, useEffect } from 'react';
import type { EmailClassification } from '@/types/email.types';

const STORAGE_KEY = 'email-classification-history';
const MAX_HISTORY_ITEMS = 100;

export function useEmailHistory() {
  const [history, setHistory] = useState<EmailClassification[]>([]);


  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);

        const historyWithDates = parsed.map((item: any) => ({
          ...item,
          email: {
            ...item.email,
            timestamp: new Date(item.email.timestamp)
          },
          processedAt: new Date(item.processedAt)
        }));
        setHistory(historyWithDates);
      }
    } catch (error) {
      console.error('Error loading history from localStorage:', error);
    }
  }, []);


  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('Error saving history to localStorage:', error);
    }
  }, [history]);

  const addToHistory = (item: EmailClassification) => {
    setHistory(prev => {
      const newHistory = [item, ...prev];

      return newHistory.slice(0, MAX_HISTORY_ITEMS);
    });
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const updateHistoryItem = (id: string, updates: Partial<EmailClassification>) => {
    setHistory(prev => 
      prev.map(item => 
        item.id === id ? { ...item, ...updates } : item
      )
    );
  };

  return {
    history,
    addToHistory,
    clearHistory,
    updateHistoryItem
  };
}
