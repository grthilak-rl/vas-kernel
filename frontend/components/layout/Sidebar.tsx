'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  HomeIcon,
  CameraIcon,
  FilmIcon,
  BookmarkIcon,
  PhotoIcon,
  CogIcon,
  ChartBarIcon,
  CubeIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Devices', href: '/devices', icon: CameraIcon },
  { name: 'Streams', href: '/streams', icon: FilmIcon },
  { name: 'AI Models', href: '/ai-models', icon: CubeIcon },
  { name: 'Snapshots', href: '/snapshots', icon: PhotoIcon },
  { name: 'Bookmarks', href: '/bookmarks', icon: BookmarkIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:absolute md:inset-y-0 md:left-0 z-40">
      <div className="flex-1 flex flex-col bg-gray-900 border-r border-gray-700">
        <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto bg-gray-900 rounded-br-2xl">
          <nav className="mt-2 flex-1 px-2 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href || 
                              (item.href !== '/' && pathname?.startsWith(item.href));
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                    ${isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }
                  `}
                >
                  <item.icon className="mr-3 h-6 w-6" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex-shrink-0 flex border-t border-gray-800 p-4 bg-gray-900 rounded-bl-2xl">
          <div className="flex-shrink-0 w-full group block">
            <div className="flex items-center">
              <div>
                <div className="flex items-center">
                  <div className="inline-block h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                    <span className="text-white font-bold">A</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-white">Admin User</p>
                    <p className="text-xs text-gray-400">admin@vas.local</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

