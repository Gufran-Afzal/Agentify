import React, { useState, useEffect } from 'react';
import { NavView, DashboardStats } from './types';
import { api } from './api/client';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';

import { DashboardPage } from './pages/DashboardPage';
import { StoreSettingsPage } from './pages/StoreSettingsPage';
import { ProductsPage } from './pages/ProductsPage';
import { KeywordsPage } from './pages/KeywordsPage';
import { ResearchPage } from './pages/ResearchPage';
import { OpportunitiesPage } from './pages/OpportunitiesPage';
import { CompetitorsPage } from './pages/CompetitorsPage';
import { BriefsPage } from './pages/BriefsPage';
import { DraftsPage } from './pages/DraftsPage';
import { PublishedPage } from './pages/PublishedPage';
import { PublicArticlePage } from './pages/PublicArticlePage';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<NavView>('dashboard');
  const [publicSlug, setPublicSlug] = useState<string>('');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Check URL pathname for /blog/:slug on initial load
  useEffect(() => {
    const path = window.location.pathname;
    if (path.startsWith('/blog/')) {
      const slug = path.replace('/blog/', '').trim();
      if (slug) {
        setPublicSlug(slug);
        setCurrentView('public-blog');
      }
    }
  }, []);

  const loadStats = async () => {
    try {
      setLoadingStats(true);
      const data = await api.getStats();
      setStats(data);
    } catch {
      // ignore
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [currentView]);

  const handleNavigate = (view: NavView) => {
    setCurrentView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleOpenPublicArticle = (slug: string) => {
    setPublicSlug(slug);
    setCurrentView('public-blog');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        currentView={currentView}
        onNavigate={handleNavigate}
        stats={stats}
      />

      {/* Main Content Pane */}
      <div className="main-wrapper">
        <Header
          currentView={currentView}
          onRefresh={loadStats}
          loading={loadingStats}
        />

        <main className="content-body">
          {currentView === 'dashboard' && (
            <DashboardPage stats={stats} onNavigate={handleNavigate} />
          )}

          {currentView === 'stores' && <StoreSettingsPage />}

          {currentView === 'products' && <ProductsPage />}

          {currentView === 'keywords' && <KeywordsPage />}

          {currentView === 'research' && <ResearchPage />}

          {currentView === 'opportunities' && (
            <OpportunitiesPage onNavigate={handleNavigate} />
          )}

          {currentView === 'competitors' && (
            <CompetitorsPage />
          )}

          {currentView === 'briefs' && (
            <BriefsPage onNavigate={handleNavigate} />
          )}

          {currentView === 'drafts' && (
            <DraftsPage onNavigate={handleNavigate} />
          )}

          {currentView === 'published' && (
            <PublishedPage onOpenPublicArticle={handleOpenPublicArticle} />
          )}

          {currentView === 'public-blog' && (
            <PublicArticlePage
              slug={publicSlug}
              onBack={() => handleNavigate('published')}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
