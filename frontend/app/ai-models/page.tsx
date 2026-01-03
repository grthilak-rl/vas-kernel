/**
 * Phase 8.3 – Frontend Model Selection UI
 *
 * This page provides control-plane UI for managing camera-to-AI-model assignment INTENT.
 *
 * CRITICAL CONSTRAINTS:
 * - This manages INTENT only, not execution state
 * - Assignment != Execution (models may be assigned but not running)
 * - No direct control of StreamAgents or model containers
 * - No assumptions about inference runtime
 * - Changes persist via Phase 8.1 backend APIs
 * - Reconciliation (Phase 8.2) eventually reflects changes in execution
 */
'use client';

import { useState, useEffect } from 'react';
import {
  getDevices,
  Device,
  listAIModelAssignments,
  createAIModelAssignment,
  updateAIModelAssignment,
  deleteAIModelAssignment,
  AIModelAssignment,
} from '@/lib/api';
import {
  CubeIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

// Phase 8.3: Available AI models (hardcoded for now)
// In future phases, this could be fetched from a model registry endpoint
const AVAILABLE_MODELS = [
  {
    id: 'yolov8-person-detection',
    name: 'YOLOv8 Person Detection',
    description: 'Detect and track people in video streams',
  },
  {
    id: 'vehicle-detection',
    name: 'Vehicle Detection',
    description: 'Detect vehicles (cars, trucks, motorcycles)',
  },
  {
    id: 'license-plate-recognition',
    name: 'License Plate Recognition',
    description: 'Read and extract license plate numbers',
  },
  {
    id: 'face-detection',
    name: 'Face Detection',
    description: 'Detect human faces in frames',
  },
];

export default function AIModelsPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [assignments, setAssignments] = useState<AIModelAssignment[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<AIModelAssignment | null>(null);

  // Form state for adding assignment
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [desiredFps, setDesiredFps] = useState<string>('');
  const [priority, setPriority] = useState<string>('');

  // Load devices and assignments on mount
  useEffect(() => {
    loadDevices();
    loadAssignments();
  }, []);

  const loadDevices = async () => {
    try {
      const data = await getDevices();
      setDevices(data);
      if (data.length > 0 && !selectedCamera) {
        setSelectedCamera(data[0].id);
      }
    } catch (err: any) {
      console.warn('[Phase 8.3] Failed to load devices:', err.message);
    }
  };

  const loadAssignments = async () => {
    setIsLoading(true);
    try {
      const response = await listAIModelAssignments({ limit: 1000 });
      setAssignments(response.assignments);
      setError(null);
    } catch (err: any) {
      // Silent failure - assignment data unavailable is not critical
      console.warn('[Phase 8.3] Failed to load assignments:', err.message);
      setAssignments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getCameraAssignments = (cameraId: string) => {
    return assignments.filter((a) => a.camera_id === cameraId);
  };

  const handleAddAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCamera || !selectedModel) return;

    setError(null);
    try {
      await createAIModelAssignment({
        camera_id: selectedCamera,
        model_id: selectedModel,
        enabled: true,
        desired_fps: desiredFps ? parseInt(desiredFps) : undefined,
        priority: priority ? parseInt(priority) : undefined,
      });

      setSuccess('Model assignment created successfully!');
      setSelectedModel('');
      setDesiredFps('');
      setPriority('');
      setIsAddModalOpen(false);
      await loadAssignments();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to create assignment');
    }
  };

  const handleToggleEnabled = async (assignment: AIModelAssignment) => {
    try {
      await updateAIModelAssignment(assignment.id, {
        enabled: !assignment.enabled,
      });

      setSuccess(`Assignment ${!assignment.enabled ? 'enabled' : 'disabled'}!`);
      await loadAssignments();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update assignment');
    }
  };

  const handleDeleteAssignment = async (assignmentId: string) => {
    if (!confirm('Remove this model assignment? This is a control-plane change and may not stop running inference immediately.')) {
      return;
    }

    try {
      await deleteAIModelAssignment(assignmentId);
      setSuccess('Assignment removed successfully!');
      await loadAssignments();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to delete assignment');
    }
  };

  const openConfigModal = (assignment: AIModelAssignment) => {
    setEditingAssignment(assignment);
    setDesiredFps(assignment.desired_fps?.toString() || '');
    setPriority(assignment.priority?.toString() || '');
    setIsConfigModalOpen(true);
    setError(null);
  };

  const handleUpdateConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAssignment) return;

    try {
      await updateAIModelAssignment(editingAssignment.id, {
        desired_fps: desiredFps ? parseInt(desiredFps) : undefined,
        priority: priority ? parseInt(priority) : undefined,
      });

      setSuccess('Assignment configuration updated!');
      setDesiredFps('');
      setPriority('');
      setIsConfigModalOpen(false);
      setEditingAssignment(null);
      await loadAssignments();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update configuration');
    }
  };

  const selectedDevice = devices.find((d) => d.id === selectedCamera);
  const cameraAssignments = selectedCamera ? getCameraAssignments(selectedCamera) : [];
  const assignedModelIds = new Set(cameraAssignments.map((a) => a.model_id));
  const availableModels = AVAILABLE_MODELS.filter((m) => !assignedModelIds.has(m.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Model Assignments</h1>
        <p className="mt-2 text-gray-600">
          Manage camera-to-model assignment intent (control-plane only)
        </p>
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> This interface manages assignment INTENT only.
            Assignments do not reflect runtime execution state. Changes may take time to reconcile.
          </p>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <CheckCircleIcon className="h-5 w-5" />
          {success}
        </div>
      )}

      {/* Camera Selector */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Camera
        </label>
        <select
          value={selectedCamera || ''}
          onChange={(e) => setSelectedCamera(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
        >
          {devices.length === 0 && (
            <option value="">No cameras available</option>
          )}
          {devices.map((device) => (
            <option key={device.id} value={device.id}>
              {device.name} {device.location ? `(${device.location})` : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Assigned Models */}
      {selectedCamera && (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Assigned Models for {selectedDevice?.name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Models currently assigned to this camera (intent)
              </p>
            </div>
            <button
              onClick={() => setIsAddModalOpen(true)}
              disabled={availableModels.length === 0}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:bg-gray-400"
            >
              <PlusIcon className="h-5 w-5" />
              Add Model
            </button>
          </div>

          {isLoading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading assignments...</p>
            </div>
          ) : cameraAssignments.length === 0 ? (
            <div className="p-12 text-center">
              <CubeIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-4 text-gray-600">No models assigned</p>
              <p className="mt-2 text-sm text-gray-500">Click "Add Model" to assign an AI model</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {cameraAssignments.map((assignment) => {
                const model = AVAILABLE_MODELS.find((m) => m.id === assignment.model_id);
                return (
                  <div key={assignment.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-base font-medium text-gray-900">
                            {model?.name || assignment.model_id}
                          </h3>
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              assignment.enabled
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {assignment.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                        {model?.description && (
                          <p className="text-sm text-gray-600 mt-1">{model.description}</p>
                        )}
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                          {assignment.desired_fps && (
                            <span>FPS: {assignment.desired_fps}</span>
                          )}
                          {assignment.priority !== undefined && (
                            <span>Priority: {assignment.priority}</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleEnabled(assignment)}
                          className={`p-2 rounded-lg transition-colors ${
                            assignment.enabled
                              ? 'text-gray-600 hover:text-gray-900'
                              : 'text-green-600 hover:text-green-900'
                          }`}
                          title={assignment.enabled ? 'Disable' : 'Enable'}
                        >
                          {assignment.enabled ? (
                            <XCircleIcon className="h-5 w-5" />
                          ) : (
                            <CheckCircleIcon className="h-5 w-5" />
                          )}
                        </button>
                        <button
                          onClick={() => openConfigModal(assignment)}
                          className="p-2 text-blue-600 hover:text-blue-900 transition-colors"
                          title="Configure"
                        >
                          <Cog6ToothIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDeleteAssignment(assignment.id)}
                          className="p-2 text-red-600 hover:text-red-900 transition-colors"
                          title="Remove Assignment"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Add Assignment Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Add Model Assignment</h2>
              <p className="text-sm text-gray-600 mt-1">
                Assign an AI model to {selectedDevice?.name}
              </p>
            </div>

            <form onSubmit={handleAddAssignment} className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AI Model *
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  required
                >
                  <option value="">Select a model...</option>
                  {availableModels.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Desired FPS (optional)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={desiredFps}
                  onChange={(e) => setDesiredFps(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="e.g., 5"
                />
                <p className="mt-1 text-xs text-gray-500">Requested inference frame rate (1-30 FPS)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority (optional)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="e.g., 50"
                />
                <p className="mt-1 text-xs text-gray-500">Priority hint (0-100, higher = more important)</p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsAddModalOpen(false);
                    setSelectedModel('');
                    setDesiredFps('');
                    setPriority('');
                    setError(null);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Add Assignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Configure Assignment Modal */}
      {isConfigModalOpen && editingAssignment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Configure Assignment</h2>
              <p className="text-sm text-gray-600 mt-1">
                Update assignment parameters (intent only)
              </p>
            </div>

            <form onSubmit={handleUpdateConfig} className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model
                </label>
                <input
                  type="text"
                  value={
                    AVAILABLE_MODELS.find((m) => m.id === editingAssignment.model_id)?.name ||
                    editingAssignment.model_id
                  }
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Desired FPS
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={desiredFps}
                  onChange={(e) => setDesiredFps(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="Leave empty for default"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="Leave empty for default"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsConfigModalOpen(false);
                    setEditingAssignment(null);
                    setDesiredFps('');
                    setPriority('');
                    setError(null);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Update
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
