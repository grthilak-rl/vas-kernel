'use client';

import { BellIcon, CameraIcon } from '@heroicons/react/24/outline';

export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 z-50 relative">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <CameraIcon className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Video Aggregation Service
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
              <BellIcon className="h-6 w-6" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Admin User</p>
                <p className="text-xs text-gray-500">Administrator</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                <span className="text-white font-bold">A</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}


