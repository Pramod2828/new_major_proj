import React, { useState } from 'react';
import { AppLayout } from './layouts/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { TrainingPage } from './pages/TrainingPage';
import { ModelsPage } from './pages/ModelsPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { SHAPPage } from './pages/SHAPPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { AboutProjectPage } from './pages/AboutProjectPage';

export function App() {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardPage onNavigate={setCurrentTab} />;
      case 'datasets':
        return <DatasetsPage onNavigate={setCurrentTab} />;
      case 'training':
        return <TrainingPage onNavigate={setCurrentTab} />;
      case 'models':
        return <ModelsPage onNavigate={setCurrentTab} />;
      case 'analysis':
        return <AnalysisPage onNavigate={setCurrentTab} />;
      case 'shap':
        return <SHAPPage onNavigate={setCurrentTab} />;
      case 'history':
        return <HistoryPage onNavigate={setCurrentTab} />;
      case 'reports':
        return <ReportsPage onNavigate={setCurrentTab} />;
      case 'settings':
        return <SettingsPage />;
      case 'about':
        return <AboutProjectPage onNavigate={setCurrentTab} />;
      default:
        return <DashboardPage onNavigate={setCurrentTab} />;
    }
  };

  return (
    <AppLayout currentTab={currentTab} setCurrentTab={setCurrentTab}>
      {renderContent()}
    </AppLayout>
  );
}

export default App;
