import React, { useEffect, useState, useCallback } from 'react';
import { checkHealth } from './api/client.ts';
import type { HealthStatus } from './types/api.ts';
import { Navbar, type NavigationTab } from './components/layout/Navbar.tsx';
import { Footer } from './components/layout/Footer.tsx';
import { OverviewView } from './components/overview/OverviewView.tsx';
import { ProductCatalogueView } from './components/catalogue/ProductCatalogueView.tsx';
import { ReviewsView } from './components/reviews/ReviewsView.tsx';
import { FutureFeaturePlaceholder } from './components/future/FutureFeaturePlaceholder.tsx';
import { BigDataAnalyticsView } from './components/analytics/BigDataAnalyticsView.tsx';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('catalogue');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isHealthChecking, setIsHealthChecking] = useState(false);

  // Cross-view navigation state
  const [reviewsParentAsinFilter, setReviewsParentAsinFilter] = useState<string>('');
  const [reviewsAsinFilter, setReviewsAsinFilter] = useState<string>('');
  const [selectedProductAsin, setSelectedProductAsin] = useState<string | null>(null);

  // Health check: executed ONCE on mount and on user request. NO tight retry loops.
  const refreshHealth = useCallback(() => {
    setIsHealthChecking(true);
    checkHealth().then((res) => {
      setIsHealthChecking(false);
      if (res.success) {
        setHealth(res.data);
      } else {
        setHealth({
          status: 'error',
          service: 'ProductPulse API',
          version: '1.0.0',
          category_lock: 'Cell_Phones_and_Accessories',
          database: {
            status: 'not_connected',
            foreign_keys: 'unknown',
            dataset: 'unknown',
          },
        });
      }
    });
  }, []);

  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  // Navigate to reviews tab with specific parent ASIN or variant ASIN filter
  const handleSelectProductForReviews = (parentAsin: string, variantAsin?: string) => {
    setReviewsParentAsinFilter(parentAsin);
    setReviewsAsinFilter(variantAsin || '');
    setActiveTab('reviews');
  };

  // Inspect product details in individual dashboard view
  const handleInspectProduct = (parentAsin: string) => {
    setSelectedProductAsin(parentAsin);
    setActiveTab('catalogue');
  };

  const handleTabChange = (tab: NavigationTab) => {
    if (tab === 'catalogue' && activeTab === 'catalogue') {
      setSelectedProductAsin(null);
    }
    setActiveTab(tab);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={handleTabChange}
        health={health}
        isHealthChecking={isHealthChecking}
        onRefreshHealth={refreshHealth}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <OverviewView
            health={health}
            isHealthChecking={isHealthChecking}
            onRefreshHealth={refreshHealth}
            onNavigateToCatalogue={() => {
              setSelectedProductAsin(null);
              setActiveTab('catalogue');
            }}
            onNavigateToReviews={() => {
              setReviewsParentAsinFilter('');
              setActiveTab('reviews');
            }}
            onInspectProduct={handleInspectProduct}
          />
        )}

        {activeTab === 'catalogue' && (
          <ProductCatalogueView
            selectedProductAsin={selectedProductAsin}
            onSelectProduct={setSelectedProductAsin}
            onSelectProductForReviews={handleSelectProductForReviews}
          />
        )}

        {activeTab === 'reviews' && (
          <ReviewsView
            initialParentAsin={reviewsParentAsinFilter}
            initialAsin={reviewsAsinFilter}
            onClearInitialFilter={() => {
              setReviewsParentAsinFilter('');
              setReviewsAsinFilter('');
            }}
          />
        )}

        {activeTab === 'sentiment' && (
          <FutureFeaturePlaceholder
            title="Aspect-Level Sentiment Analysis"
            phaseTag="Phase 7"
            category="Cell_Phones_and_Accessories"
            description="Phase 7 will introduce verifiable sentiment classification using NLTK for text preprocessing and scikit-learn for TF-IDF baseline models. Predictions will evaluate customer opinions across core smartphone aspects (Battery Life, Camera, Build Quality, Display, Performance, Connectivity)."
            scheduledMilestones={[
              'Rule-based domain aspect extraction for mobile phones',
              'Interpretable TF-IDF + Logistic Regression / Linear SVM baseline classifiers',
              'Explicit confidence thresholds and polarity metrics',
              'Traceable quotes linked directly to source review IDs',
            ]}
            scientificConstraints={[
              'Star ratings are customer disposition baselines, never ground-truth aspect sentiment',
              'Aspect classifications require minimum token length and explicit keyword mentions',
              'Denominators must explicitly state total aspect mentions vs total reviews',
              'No paid external LLMs or black-box generative APIs',
            ]}
          />
        )}

        {activeTab === 'complaints' && (
          <FutureFeaturePlaceholder
            title="Customer Complaint Theme Discovery"
            phaseTag="Phase 8"
            category="Cell_Phones_and_Accessories"
            description="Phase 8 will implement unsupervised complaint discovery to extract high-frequency negative issue clusters grounded in authentic customer review excerpts. The system will categorize customer friction points into structured themes."
            scheduledMilestones={[
              'N-gram frequency analysis of negative sentiment sentences',
              'K-Means / HDBSCAN clustering of TF-IDF complaint vectors',
              'Complaint theme naming based on high-salience terms',
              'Evidence snippet extraction with direct clickable links to genuine reviews',
            ]}
            scientificConstraints={[
              'A complaint cluster is an empirical cluster of negative text, not a verified manufacturing flaw',
              'Single reviews with multiple complaints report distinct snippet count vs distinct review count',
              'Clusters require minimum support (N >= 5 distinct reviews) to be reported',
              'No fabricated defect statistics or unsubstantiated recall claims',
            ]}
          />
        )}

        {activeTab === 'bda' && (
          <BigDataAnalyticsView
            onInspectProduct={handleInspectProduct}
            onSelectProductForReviews={handleSelectProductForReviews}
          />
        )}
      </main>

      {/* Persistent Academic Footer */}
      <Footer />
    </div>
  );
};
