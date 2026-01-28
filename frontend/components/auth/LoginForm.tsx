"use client";

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Lock } from 'lucide-react';
import { AxiosError } from 'axios';

export function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Form encoding is standard for OAuth2 password flow which FastAPI uses by default often,
      // but the backend auth.py usually expects JSON or Form depending on implementation.
      // Based on previous curl commands in context: 
      // curl -X POST ... -d '{"username":"admin","password":"admin123"}'
      // It implies JSON body.
      
      const response = await api.post('/auth/login', {
        username,
        password,
      });

      // Response usually contains access_token
      const { access_token } = response.data;
      
      if (access_token) {
          login(access_token, username);
      } else {
          setError('Invalid response from server');
      }
    } catch (err) {
      const error = err as AxiosError<{detail: string}>;
      console.error('Login failed', error);
      if (error.response?.status === 401) {
        setError('Invalid username or password');
      } else {
        setError(error.response?.data?.detail || 'Something went wrong. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-8 rounded-xl border bg-white p-10 shadow-sm">
      <div className="flex flex-col items-center justify-center text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
            <Lock className="h-6 w-6 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-gray-900">
            Welcome back
        </h2>
        <p className="mt-2 text-sm text-gray-500">
            Please sign in to your account
        </p>
      </div>

      <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
        <div className="space-y-4">
            <div>
                <label htmlFor="username" className="mb-2 block text-sm font-medium text-gray-700">
                    Username
                </label>
                <Input
                    id="username"
                    name="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    autoComplete="username"
                />
            </div>
            <div>
                <label htmlFor="password" className="mb-2 block text-sm font-medium text-gray-700">
                    Password
                </label>
                <Input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    autoComplete="current-password"
                />
            </div>
        </div>

        {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
            </div>
        )}

        <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
        >
            {isLoading ? (
                <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                </>
            ) : (
                'Sign in'
            )}
        </Button>
        
        <div className="text-center text-xs text-gray-400 mt-4">
            Default: admin / admin123
        </div>
      </form>
    </div>
  );
}
