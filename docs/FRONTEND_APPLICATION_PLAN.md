# Frontend Application Plan

**Date**: 2026-01-27  
**Branch**: planning/front_end-012726  
**Status**: Planning Phase

## Overview

Design a Next.js web application for Product Describer with two main pages: Image Generation and Product Analysis. Modeled after the VML Brand-Based Image Generation frontend but simplified for product workflows.

---

## Technology Stack

### Core Framework
- **Next.js 16** - App Router
- **React 19** - Latest features
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Styling (CSS-first configuration)

### UI Components
- **Radix UI** - Accessible primitives (Dialog, etc.)
- **Lucide React** - Icons
- **Custom Components** - Modeled after VML Brand-Based Generation (see Design System below)

### State & Data
- **Axios** - API client
- **React Context** - Auth state
- **Local Storage** - Token persistence

---

## Design System & Styling

The application will replicate the visual style of the "VML Brand_Based_Image_Generation" project: a professional, high-density SaaS aesthetic.

### Color Palette
- **Backgrounds**: `bg-gray-50` (Sidebar), `bg-gray-100` (Main Content), `bg-white` (Cards/Panels).
- **Text**: `text-gray-900` (Headings), `text-gray-700` (Primary), `text-gray-600` (Secondary), `text-gray-400` (Metadata).
- **Primary Actions**: Blue (`text-blue-700`, `bg-blue-100` for active states).
- **Secondary Actions**: Purple (`hover:text-purple-600`, loading states).
- **Destructive**: Red (`text-red-600`, `hover:bg-red-50`).
- **Status**: Green (`text-green-500`, `bg-green-100` for active badges).

### Typography
- **Font**: Geist Sans / Geist Mono (Next.js defaults).
- **Scale**: High density focus.
  - Headings: `text-lg font-semibold`.
  - Body: `text-sm`.
  - Metadata/Labels: `text-xs` or `text-[10px]`.

### UI Patterns
- **Layout**: Fixed sidebar (w-64, border-r) + flexible main content area.
- **Cards**: `rounded-lg border bg-white shadow-sm hover:shadow-md`.
- **Buttons**:
  - Icon-only: `text-gray-500 hover:bg-gray-200 hover:text-purple-600 rounded p-1`.
  - Nav Items: `w-full rounded-md px-3 py-2 text-left text-sm`.
  - Overlay Actions: `rounded-full bg-white/80 backdrop-blur-sm shadow-sm`.
- **Feedback**: `Loader2` animate-spin icons for sync operations.

---

## Application Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with auth provider
│   ├── page.tsx                # Landing/redirect page
│   ├── login/
│   │   └── page.tsx            # Login page
│   ├── dashboard/
│   │   ├── layout.tsx          # Authenticated layout
│   │   ├── page.tsx            # Redirect to /generate
│   │   ├── generate/
│   │   │   └── page.tsx        # Image Generation page (Page 1)
│   │   └── analyze/
│   │       └── page.tsx        # Product Analysis page (Page 2)
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── ProtectedRoute.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── generate/
│   │   ├── ProductSelector.tsx
│   │   ├── ReferenceImages.tsx
│   │   ├── PromptInput.tsx
│   │   ├── GenerationControls.tsx
│   │   └── ImageGallery.tsx
│   ├── analyze/
│   │   ├── ImageUploader.tsx
│   │   ├── AnalysisProgress.tsx
│   │   ├── YamlEditor.tsx
│   │   └── SpecificationViewer.tsx
│   └── ui/
│       ├── button.tsx
│       ├── input.tsx
│       ├── dialog.tsx
│       └── ...
├── hooks/
│   ├── useAuth.ts
│   ├── useProducts.ts
│   ├── useGeneration.ts
│   └── useAnalysis.ts
├── lib/
│   ├── api.ts                  # Axios instance
│   ├── auth.ts                 # Auth utilities
│   └── types.ts                # TypeScript types
└── contexts/
    └── AuthContext.tsx
```

---

## Page Designs

### Login Page (`/login`)

**Purpose**: Authenticate users before accessing the application.

**Features**:
- Simple username/password form
- Default credentials: admin/admin123
- JWT token storage in localStorage
- Redirect to /dashboard/generate on success

**UI Layout**:
```
┌─────────────────────────────────────┐
│                                     │
│         Product Describer           │
│                                     │
│    ┌─────────────────────────┐     │
│    │  Username: [_______]    │     │
│    │  Password: [_______]    │     │
│    │                         │     │
│    │     [  Login  ]         │     │
│    └─────────────────────────┘     │
│                                     │
└─────────────────────────────────────┘
```

**Component Breakdown**:
```tsx
// app/login/page.tsx
export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <LoginForm />
    </div>
  );
}

// components/auth/LoginForm.tsx
export function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post('/api/auth/login', { username, password });
      localStorage.setItem('token', response.data.access_token);
      router.push('/dashboard/generate');
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-8 bg-white rounded-lg shadow">
      <h1>Login to Product Describer</h1>
      <input type="text" placeholder="Username" value={username} onChange={...} />
      <input type="password" placeholder="Password" value={password} onChange={...} />
      {error && <p className="text-red-500">{error}</p>}
      <button type="submit">Login</button>
    </form>
  );
}
```

---

### Page 1: Image Generation (`/dashboard/generate`)

**Purpose**: Generate images from existing product specifications.

**Features**:
1. **Product Selector** - Dropdown of available products
2. **Reference Images Display** - Show uploaded product reference images
3. **Prompt Input** - Text area for custom generation prompt
4. **Generation Controls**:
   - Aspect Ratio selector (1:1, 16:9, 4:3, 9:16)
   - Number of generations (1-10)
   - Generate button
5. **Image Gallery** - Grid display of generated images with download

**UI Layout**:
```
┌──────────────────────────────────────────────────────────────┐
│ [Logo] Product Describer        Generate | Analyze  [Logout] │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│ Product: [Stasher Half Gallon ▾]                             │
│                                                                │
│ ┌─ Reference Images ────────────────────────────────────┐    │
│ │  [img1] [img2] [img3] [img4] [img5]                  │    │
│ └────────────────────────────────────────────────────────┘    │
│                                                                │
│ ┌─ Generation Prompt ───────────────────────────────────┐    │
│ │  Create a professional studio photograph...           │    │
│ │  [                                                    ]│    │
│ │  [                                                    ]│    │
│ └────────────────────────────────────────────────────────┘    │
│                                                                │
│  Aspect Ratio: [1:1 ▾]    Count: [3 ▾]   [ Generate ]       │
│                                                                │
│ ┌─ Generated Images (12) ───────────────────────────────┐    │
│ │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                     │    │
│ │  │img  │ │img  │ │img  │ │img  │                     │    │
│ │  │ [↓] │ │ [↓] │ │ [↓] │ │ [↓] │                     │    │
│ │  └─────┘ └─────┘ └─────┘ └─────┘                     │    │
│ │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                     │    │
│ │  │img  │ │img  │ │img  │ │img  │                     │    │
│ │  └─────┘ └─────┘ └─────┘ └─────┘                     │    │
│ └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

**Component Structure**:
```tsx
// app/dashboard/generate/page.tsx
export default function GeneratePage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [count, setCount] = useState(1);
  const [generations, setGenerations] = useState<GeneratedImage[]>([]);

  return (
    <div className="p-6 space-y-6">
      <ProductSelector
        value={selectedProduct}
        onChange={setSelectedProduct}
      />
      
      {selectedProduct && (
        <>
          <ReferenceImages productId={selectedProduct.id} />
          
          <PromptInput
            value={prompt}
            onChange={setPrompt}
            placeholder="Create a professional studio photograph..."
          />
          
          <GenerationControls
            aspectRatio={aspectRatio}
            setAspectRatio={setAspectRatio}
            count={count}
            setCount={setCount}
            onGenerate={handleGenerate}
            disabled={!prompt}
          />
          
          <ImageGallery
            images={generations}
            onDownload={handleDownload}
          />
        </>
      )}
    </div>
  );
}
```

**Key Components**:

```tsx
// components/generate/ProductSelector.tsx
export function ProductSelector({ value, onChange }) {
  const { data: products } = useProducts();
  
  return (
    <select value={value?.id} onChange={(e) => onChange(products.find(p => p.id === e.target.value))}>
      <option value="">Select a product...</option>
      {products?.map(p => (
        <option key={p.id} value={p.id}>{p.name}</option>
      ))}
    </select>
  );
}

// components/generate/ReferenceImages.tsx
export function ReferenceImages({ productId }) {
  const { data: references } = useQuery(
    ['references', productId],
    () => api.get(`/products/${productId}/references`)
  );
  
  return (
    <div className="flex gap-2 overflow-x-auto">
      {references?.map(ref => (
        <img
          key={ref.id}
          src={ref.url}
          alt={ref.filename}
          className="h-24 w-24 object-cover rounded"
        />
      ))}
    </div>
  );
}

// components/generate/PromptInput.tsx
export function PromptInput({ value, onChange, placeholder }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={4}
      className="w-full p-3 border rounded"
    />
  );
}

// components/generate/GenerationControls.tsx
export function GenerationControls({
  aspectRatio,
  setAspectRatio,
  count,
  setCount,
  onGenerate,
  disabled
}) {
  return (
    <div className="flex gap-4 items-center">
      <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)}>
        <option value="1:1">Square (1:1)</option>
        <option value="16:9">Landscape (16:9)</option>
        <option value="4:3">Standard (4:3)</option>
        <option value="9:16">Portrait (9:16)</option>
      </select>
      
      <select value={count} onChange={(e) => setCount(Number(e.target.value))}>
        {[1, 2, 3, 4, 5].map(n => (
          <option key={n} value={n}>{n} image{n > 1 ? 's' : ''}</option>
        ))}
      </select>
      
      <button
        onClick={onGenerate}
        disabled={disabled}
        className="px-6 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        Generate
      </button>
    </div>
  );
}

// components/generate/ImageGallery.tsx
export function ImageGallery({ images, onDownload }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {images.map(img => (
        <div key={img.id} className="relative group">
          <img src={img.url} alt={img.filename} className="w-full rounded" />
          <button
            onClick={() => onDownload(img)}
            className="absolute bottom-2 right-2 p-2 bg-white rounded opacity-0 group-hover:opacity-100"
          >
            <Download size={20} />
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

### Page 2: Product Analysis (`/dashboard/analyze`)

**Purpose**: Upload product images and run GPT Vision analysis to create/update specifications.

**Features**:
1. **Product Creation/Selection**
   - Create new product or select existing
   - Product name and slug input
2. **Image Uploader**
   - Drag-and-drop or click to upload
   - Multiple image support
   - Preview thumbnails
3. **Analysis Trigger**
   - "Analyze Product" button
   - Progress indicator during analysis
4. **Specification Viewer/Editor**
   - YAML display with syntax highlighting
   - Editable text area
   - Save/Create New Version button
   - Version history dropdown
5. **Derived Info Display**
   - Key dimensions
   - Primary colors
   - Material type
   - Confidence score

**UI Layout**:
```
┌──────────────────────────────────────────────────────────────┐
│ [Logo] Product Describer        Generate | Analyze  [Logout] │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌─ Product Setup ───────────────────────────────────────┐    │
│ │  ○ Create New Product                                 │    │
│ │    Name: [________________]  Slug: [_____________]    │    │
│ │  ○ Use Existing: [Select Product ▾]                   │    │
│ └────────────────────────────────────────────────────────┘    │
│                                                                │
│ ┌─ Upload Reference Images ─────────────────────────────┐    │
│ │  ┌─────────────────────────────────────────────┐      │    │
│ │  │ Drag & drop images here or click to browse │      │    │
│ │  └─────────────────────────────────────────────┘      │    │
│ │  [thumb1] [thumb2] [thumb3] [×] [×] [×]               │    │
│ └────────────────────────────────────────────────────────┘    │
│                                                                │
│  [ Analyze Product ]  Status: Ready / Analyzing... / Done    │
│                                                                │
│ ┌─ Specification (v2) ──────────────┬─ Quick Info ──────┐   │
│ │ metadata:                         │ Dimensions:        │   │
│ │   template_version: '1.0'         │   215.9 × 260.35mm │   │
│ │   product_name: stasher_half_...  │                    │   │
│ │   confidence_overall: 0.78        │ Material:          │   │
│ │                                    │   Silicone         │   │
│ │ dimensions:                        │                    │   │
│ │   primary:                         │ Colors:            │   │
│ │     width:                         │   #CFE7EE          │   │
│ │       value: 215.9                 │   #FFFFFF          │   │
│ │       ...                          │                    │   │
│ │                                    │ Confidence: 78%    │   │
│ │                                    │                    │   │
│ │ [Version: v2 ▾]  [ Save Changes ] │                    │   │
│ └────────────────────────────────────┴────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**Component Structure**:
```tsx
// app/dashboard/analyze/page.tsx
export default function AnalyzePage() {
  const [mode, setMode] = useState<'create' | 'existing'>('create');
  const [productName, setProductName] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [images, setImages] = useState<File[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [specification, setSpecification] = useState<string>('');

  const handleAnalyze = async () => {
    setAnalyzing(true);
    // Upload images, trigger analysis, get spec
    const result = await analyzeProduct(productId, images);
    setSpecification(result.yaml_content);
    setAnalyzing(false);
  };

  return (
    <div className="p-6 space-y-6">
      <ProductSetup
        mode={mode}
        onModeChange={setMode}
        productName={productName}
        onProductNameChange={setProductName}
        selectedProduct={selectedProduct}
        onProductChange={setSelectedProduct}
      />
      
      <ImageUploader
        images={images}
        onImagesChange={setImages}
      />
      
      <button
        onClick={handleAnalyze}
        disabled={!canAnalyze}
        className="btn-primary"
      >
        {analyzing ? 'Analyzing...' : 'Analyze Product'}
      </button>
      
      {specification && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <YamlEditor
              value={specification}
              onChange={setSpecification}
              onSave={handleSave}
            />
          </div>
          <div>
            <SpecificationSummary yaml={specification} />
          </div>
        </div>
      )}
    </div>
  );
}
```

**Key Components**:

```tsx
// components/analyze/ImageUploader.tsx
export function ImageUploader({ images, onImagesChange }) {
  const onDrop = useCallback((acceptedFiles) => {
    onImagesChange([...images, ...acceptedFiles]);
  }, [images]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg'] },
    multiple: true
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
      >
        <input {...getInputProps()} />
        <p>Drag & drop images here or click to browse</p>
      </div>
      
      <div className="flex gap-2 mt-4">
        {images.map((img, i) => (
          <div key={i} className="relative">
            <img src={URL.createObjectURL(img)} className="h-20 w-20 object-cover rounded" />
            <button
              onClick={() => onImagesChange(images.filter((_, idx) => idx !== i))}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// components/analyze/YamlEditor.tsx
export function YamlEditor({ value, onChange, onSave }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <h3>Specification YAML</h3>
        <button onClick={onSave} className="btn-primary">
          Save Changes (New Version)
        </button>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-96 font-mono text-sm p-4 border rounded"
      />
    </div>
  );
}

// components/analyze/SpecificationSummary.tsx
export function SpecificationSummary({ yaml }) {
  const parsed = useMemo(() => YAML.parse(yaml), [yaml]);
  
  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded">
      <div>
        <h4 className="font-semibold">Dimensions</h4>
        <p>{parsed.dimensions?.primary?.width?.value} × {parsed.dimensions?.primary?.height?.value}mm</p>
      </div>
      
      <div>
        <h4 className="font-semibold">Material</h4>
        <p>{parsed.materials?.primary_material?.type}</p>
      </div>
      
      <div>
        <h4 className="font-semibold">Primary Colors</h4>
        <div className="flex gap-2">
          {parsed.colors?.primary?.hex && (
            <div
              className="w-8 h-8 rounded border"
              style={{ backgroundColor: parsed.colors.primary.hex }}
            />
          )}
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold">Confidence</h4>
        <p>{(parsed.metadata?.confidence_overall * 100).toFixed(0)}%</p>
      </div>
    </div>
  );
}
```

---

## Navigation & Layout

### Header Component
```tsx
// components/layout/Header.tsx
export function Header() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  
  return (
    <header className="border-b bg-white">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-8">
          <h1 className="text-xl font-bold">Product Describer</h1>
          <nav className="flex gap-4">
            <Link
              href="/dashboard/generate"
              className={pathname === '/dashboard/generate' ? 'font-bold' : ''}
            >
              Generate
            </Link>
            <Link
              href="/dashboard/analyze"
              className={pathname === '/dashboard/analyze' ? 'font-bold' : ''}
            >
              Analyze
            </Link>
          </nav>
        </div>
        
        <div className="flex items-center gap-4">
          <span>{user?.username}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </div>
    </header>
  );
}
```

---

## API Integration

### Axios Client Setup
```tsx
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Custom Hooks
```tsx
// hooks/useProducts.ts
export function useProducts() {
  return useQuery(['products'], async () => {
    const { data } = await api.get('/products');
    return data;
  });
}

// hooks/useGeneration.ts
export function useGeneration() {
  const queryClient = useQueryClient();
  
  return useMutation(
    async (params: GenerationParams) => {
      const { data } = await api.post(`/products/${params.productId}/generate`, params);
      return data;
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['generations']);
      }
    }
  );
}

// hooks/useAnalysis.ts
export function useAnalysis() {
  return useMutation(
    async ({ productId, images }: { productId: number; images: File[] }) => {
      const formData = new FormData();
      images.forEach(img => formData.append('images', img));
      
      const { data } = await api.post(`/products/${productId}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return data;
    }
  );
}
```

---

## Styling & Theme

### Tailwind Configuration
```js
// tailwind.config.js
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
};
```

### Global Styles
```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50;
  }
  
  .btn-secondary {
    @apply px-4 py-2 border border-gray-300 rounded hover:bg-gray-50;
  }
  
  .card {
    @apply bg-white rounded-lg shadow p-6;
  }
}
```

---

## Development Workflow

### Project Setup
```bash
# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --app

# Install dependencies
cd frontend
npm install axios @radix-ui/react-dialog lucide-react clsx tailwind-merge
npm install -D @types/node

# Environment setup
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Run dev server
npm run dev
```

### Testing Strategy
```tsx
// components/auth/LoginForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('should submit credentials', async () => {
    render(<LoginForm />);
    
    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'admin' }
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'admin123' }
    });
    fireEvent.click(screen.getByText('Login'));
    
    // Assert API call made
  });
});
```

---

## Deployment Considerations

### Docker Support
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables
```env
# Production
NEXT_PUBLIC_API_URL=https://api.productdescriber.com
```

---

## Success Criteria

- [ ] User can login with admin/admin123
- [ ] Generate page shows products and references
- [ ] User can input prompt and generate images
- [ ] Images appear in gallery with download
- [ ] Analyze page allows product creation
- [ ] User can upload multiple images
- [ ] Analysis triggers and returns YAML
- [ ] YAML is editable and saveable
- [ ] Version history works
- [ ] Navigation between pages works
- [ ] Logout clears auth state

---

## Next Steps

1. ✅ Database planning complete
2. ✅ Frontend planning complete
3. ⏳ **Backend Implementation**:
   - Set up FastAPI project
   - Implement database models
   - Create API endpoints
   - Add authentication
4. ⏳ **Frontend Implementation**:
   - Initialize Next.js project
   - Build authentication flow
   - Create Generate page
   - Create Analyze page
5. ⏳ **Integration**:
   - Connect frontend to API
   - Test full workflow
   - Deploy
