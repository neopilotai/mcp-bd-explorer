'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, Check } from 'lucide-react';

interface ExportFilters {
  category: string;
  [key: string]: unknown;
}

interface ExportModalProps {
  onClose: () => void;
  query: string;
  filters: ExportFilters;
}

export default function ExportModal({ onClose, query, filters }: ExportModalProps) {
  const [format, setFormat] = useState('csv');
  const [isExporting, setIsExporting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    // Simulate export process
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsExporting(false);
    setIsComplete(true);
    setTimeout(() => {
      onClose();
      setIsComplete(false);
    }, 1000);
  };

  const formats = [
    { id: 'csv', label: 'CSV', description: 'Spreadsheet compatible format' },
    { id: 'json', label: 'JSON', description: 'Structured data format' },
    { id: 'excel', label: 'Excel', description: 'Microsoft Excel format' },
    { id: 'pdf', label: 'PDF Report', description: 'Formatted report' },
  ];

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-foreground">Export Results</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="space-y-2 text-sm">
            <p className="text-muted-foreground">Query: {query}</p>
            <p className="text-muted-foreground">Category: {filters.category}</p>
          </div>

          <Tabs value={format} onValueChange={setFormat} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              {formats.map((f) => (
                <TabsTrigger key={f.id} value={f.id} className="text-xs">
                  {f.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {formats.map((f) => (
              <TabsContent key={f.id} value={f.id}>
                <div className="p-4 bg-card/50 border border-border/60 rounded-lg text-center">
                  <p className="text-sm font-medium text-foreground mb-1">{f.label}</p>
                  <p className="text-xs text-muted-foreground">{f.description}</p>
                </div>
              </TabsContent>
            ))}
          </Tabs>

          <Button
            onClick={handleExport}
            disabled={isExporting || isComplete}
            className="w-full"
            variant={isComplete ? 'outline' : 'default'}
          >
            {isComplete ? (
              <>
                <Check className="w-4 h-4 mr-2" />
                Exported Successfully
              </>
            ) : isExporting ? (
              <>
                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin mr-2" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export Now
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
