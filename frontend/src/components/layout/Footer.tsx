import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-semibold text-slate-700">ProductPulse</span> — Academic Big Data Analytics &amp; NLP Platform
            <span className="mx-2 text-slate-300">•</span>
            Category Lock: <code className="bg-slate-100 text-slate-800 px-1 py-0.5 rounded font-mono">Cell_Phones_and_Accessories</code>
          </div>
          <div className="text-center md:text-right">
            Dataset Source: <a href="https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023" target="_blank" rel="noreferrer" className="underline hover:text-brand-600">McAuley-Lab/Amazon-Reviews-2023</a>
            <span className="mx-2 text-slate-300">•</span>
            Non-Fabrication Policy Enforced
          </div>
        </div>
      </div>
    </footer>
  );
};
