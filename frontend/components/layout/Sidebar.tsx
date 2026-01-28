import NextLink from 'next/link';
import { usePathname } from 'next/navigation';
import { Package, Image as ImageIcon, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';

export function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();
  
  const navItems = [
    { name: 'Generate', href: '/dashboard/generate', icon: ImageIcon },
    { name: 'Analyze', href: '/dashboard/analyze', icon: Package },
  ];

  return (
    <div className="flex h-screen w-64 flex-col border-r bg-gray-50 text-gray-900">
      <div className="flex h-14 items-center border-b px-4">
        <span className="text-lg font-bold tracking-tight">Product Describer</span>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
            {navItems.map((item) => {
                const isActive = pathname.startsWith(item.href);
                return (
                    <NextLink
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                            isActive 
                                ? "bg-blue-100 text-blue-700" 
                                : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                        )}
                    >
                        <item.icon className={cn(
                            "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                            isActive ? "text-blue-500" : "text-gray-400 group-hover:text-gray-500"
                        )} />
                        {item.name}
                    </NextLink>
                );
            })}
        </nav>
      </div>

      <div className="border-t p-4">
        <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white text-xs font-bold">
                {user?.username.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium text-gray-900">{user?.username}</p>
                <p className="truncate text-xs text-gray-500">User</p>
            </div>
            <button 
                onClick={logout}
                className="text-gray-400 hover:text-red-600 transition-colors"
                title="Log out"
            >
                <LogOut className="h-5 w-5" />
            </button>
        </div>
      </div>
    </div>
  );
}
