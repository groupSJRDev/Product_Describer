"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    // Default redirect to generate page
    router.push('/dashboard/generate');
  }, [router]);

  return null;
}
