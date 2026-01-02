// ============================================================================
// Phase 6.3: AI Overlay Controls UI Component
// ============================================================================
// User interface for controlling AI overlay visualization settings.
// Provides toggles, sliders, and filters for customizing overlay appearance.
// All controls are client-side only and do not affect backend behavior.

'use client';

import { useState } from 'react';
import { OverlaySettings } from '@/hooks/useOverlaySettings';

interface AIOverlayControlsProps {
  /**
   * Current overlay settings
   */
  settings: OverlaySettings;

  /**
   * Available model IDs for filtering
   * Extracted from AI events
   */
  availableModels?: string[];

  /**
   * Callback when settings are updated
   */
  onUpdateSettings: (updates: Partial<OverlaySettings>) => void;

  /**
   * Callback to reset settings to defaults
   */
  onResetSettings: () => void;

  /**
   * Optional className for styling
   */
  className?: string;
}

/**
 * Phase 6.3: AI Overlay Controls Component
 *
 * Provides user interface for:
 * - Global overlay enable/disable toggle
 * - Confidence threshold slider
 * - Label visibility toggles
 * - Model filtering
 * - Visual customization (opacity, color, line width)
 *
 * All settings are applied client-side only and do not affect:
 * - AI inference or execution
 * - Backend data storage
 * - Video playback
 *
 * @example
 * <AIOverlayControls
 *   settings={settings}
 *   availableModels={['yolov8', 'efficientdet']}
 *   onUpdateSettings={updateSettings}
 *   onResetSettings={resetSettings}
 * />
 */
export function AIOverlayControls({
  settings,
  availableModels = [],
  onUpdateSettings,
  onResetSettings,
  className = '',
}: AIOverlayControlsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  /**
   * Check if a model is currently visible
   */
  const isModelVisible = (modelId: string): boolean => {
    // Empty visibleModels = show all
    if (settings.visibleModels.length === 0) {
      return true;
    }
    return settings.visibleModels.includes(modelId);
  };

  /**
   * Toggle model visibility
   */
  const handleToggleModel = (modelId: string) => {
    const visible = settings.visibleModels;
    if (visible.length === 0) {
      // Showing all → show only this model
      onUpdateSettings({ visibleModels: [modelId] });
    } else if (visible.includes(modelId)) {
      // Model visible → hide it
      const updated = visible.filter((id) => id !== modelId);
      onUpdateSettings({ visibleModels: updated });
    } else {
      // Model hidden → show it
      onUpdateSettings({ visibleModels: [...visible, modelId] });
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header with main toggle */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enabled}
                onChange={(e) => onUpdateSettings({ enabled: e.target.checked })}
                className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-900">
                Show AI Overlays
              </span>
            </label>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
            >
              {isExpanded ? 'Hide Settings' : 'Show Settings'}
            </button>
            <button
              onClick={onResetSettings}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
              title="Reset to defaults"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Expanded settings */}
      {isExpanded && settings.enabled && (
        <div className="p-4 space-y-4">
          {/* Label visibility toggles */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-900">Display Options</h4>
            <div className="flex flex-col gap-2">
              <label className="inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.showLabels}
                  onChange={(e) => onUpdateSettings({ showLabels: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600"
                />
                <span className="ml-2 text-sm text-gray-700">Show class labels</span>
              </label>
              <label className="inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.showConfidence}
                  onChange={(e) => onUpdateSettings({ showConfidence: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600"
                />
                <span className="ml-2 text-sm text-gray-700">Show confidence scores</span>
              </label>
            </div>
          </div>

          {/* Confidence threshold slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-900">
                Confidence Threshold
              </label>
              <span className="text-sm text-gray-600">
                {Math.round(settings.confidenceThreshold * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={settings.confidenceThreshold * 100}
              onChange={(e) => onUpdateSettings({ confidenceThreshold: parseInt(e.target.value) / 100 })}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-500">
              Hide detections below this confidence level
            </p>
          </div>

          {/* Model filtering */}
          {availableModels.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-900">Model Filter</h4>
                {settings.visibleModels.length > 0 && (
                  <button
                    onClick={() => onUpdateSettings({ visibleModels: [] })}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Show All
                  </button>
                )}
              </div>
              <div className="flex flex-col gap-2 max-h-32 overflow-y-auto">
                {availableModels.map((modelId) => (
                  <label key={modelId} className="inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isModelVisible(modelId)}
                      onChange={() => handleToggleModel(modelId)}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600"
                    />
                    <span className="ml-2 text-sm text-gray-700 truncate" title={modelId}>
                      {modelId}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Visual customization */}
          <div className="space-y-3 pt-3 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900">Appearance</h4>

            {/* Box opacity */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-700">Box Opacity</label>
                <span className="text-xs text-gray-600">
                  {Math.round(settings.boxOpacity * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.boxOpacity * 100}
                onChange={(e) => onUpdateSettings({ boxOpacity: parseInt(e.target.value) / 100 })}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Label opacity */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-700">Label Opacity</label>
                <span className="text-xs text-gray-600">
                  {Math.round(settings.labelOpacity * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.labelOpacity * 100}
                onChange={(e) => onUpdateSettings({ labelOpacity: parseInt(e.target.value) / 100 })}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Box line width */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-700">Line Width</label>
                <span className="text-xs text-gray-600">
                  {settings.boxLineWidth}px
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={settings.boxLineWidth}
                onChange={(e) => onUpdateSettings({ boxLineWidth: parseInt(e.target.value) })}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Box color */}
            <div className="space-y-1">
              <label className="text-xs text-gray-700">Box Color</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={settings.boxColor}
                  onChange={(e) => onUpdateSettings({ boxColor: e.target.value })}
                  className="w-12 h-8 rounded border border-gray-300 cursor-pointer"
                />
                <span className="text-xs text-gray-600 font-mono">{settings.boxColor}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Disabled state hint */}
      {isExpanded && !settings.enabled && (
        <div className="p-4 text-center text-sm text-gray-500 italic">
          Enable AI overlays to access settings
        </div>
      )}
    </div>
  );
}
