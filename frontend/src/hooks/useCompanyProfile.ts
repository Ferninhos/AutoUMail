import { useState, useEffect } from 'react';

export interface CompanyProfile {
  config_id?: string;
  company_name: string;
  custom_instructions: string;
}

const STORAGE_KEY = 'company_profile';

export function useCompanyProfile() {
  const [profile, setProfile] = useState<CompanyProfile | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  });

  const saveProfile = (newProfile: CompanyProfile) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newProfile));
    setProfile(newProfile);
  };

  const clearProfile = () => {
    localStorage.removeItem(STORAGE_KEY);
    setProfile(null);
  };

  return { profile, saveProfile, clearProfile };
}
