# Frontend — React Application

## Purpose

Frontend SPA (Single Page Application) cho hệ thống Student-Document-OCR.
Giao diện người dùng để upload tài liệu, xem kết quả OCR, tìm kiếm full-text và quản lý.

## Scope

React + Vite + TypeScript SPA chạy trên port 3000:

| Module | Công nghệ | Mô tả |
|--------|-----------|-------|
| Framework | React 18 + Vite | SPA với HMR |
| Language | TypeScript | Type safety |
| Routing | React Router v6 | Client-side routing |
| Server State | TanStack Query | API cache, refetch, mutation |
| Client State | Zustand | Auth store, UI state |
| Forms | React Hook Form + Zod | Validation |
| HTTP Client | Axios | API client với interceptors |
| UI Components | Custom / shadcn-ui | Design system |
| Build | Vite | Fast dev server, ESM |

## Cấu trúc thư mục (planned)

```
frontend/
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Router setup
│   ├── features/             # Feature-based modules
│   │   ├── auth/             # Login, logout, token refresh
│   │   ├── documents/        # Upload, list, detail, OCR viewer
│   │   └── search/           # Search page, filter, highlight
│   ├── components/           # Shared UI components
│   ├── hooks/                # Custom React hooks
│   ├── services/             # Axios API client
│   ├── stores/               # Zustand stores
│   ├── types/                # TypeScript interfaces
│   └── utils/                # Helper functions
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── Dockerfile
```

## TODO

- [ ] Khởi tạo Vite React + TypeScript project
- [ ] Cấu hình path aliases (`@/` → `src/`)
- [ ] Setup React Router v6 với protected routes
- [ ] Implement Axios client với JWT interceptor (auto refresh)
- [ ] Implement Auth feature (Login page, useAuth store)
- [ ] Implement Document Upload (drag-and-drop, progress bar)
- [ ] Implement Document List với thumbnail và status badge
- [ ] Implement OCR Viewer (text overlay trên ảnh)
- [ ] Implement Search page (search bar, filter, highlighted results)
- [ ] Viết Dockerfile (multi-stage: build → nginx)
- [ ] Responsive design (mobile-first)

## References

- Architecture.md
- React.md
- ComponentGuide.md
- StateManagement.md
- UI.md
- .ai/design/UI.md
- .ai/design/API.md
