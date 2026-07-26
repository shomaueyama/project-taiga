import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { App } from "./routes/App";
import "./styles.css";

const queryClient = new QueryClient();
const router = createBrowserRouter([{ path: "*", element: <App /> }]);
const rootElement = document.getElementById("root");

class RootErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="fatal-shell">
          <section className="fatal-panel" role="alert">
            <h1>画面を読み込めません</h1>
            <p>ブラウザを更新してください。直らない場合は Shoma に知らせてください。</p>
            <button type="button" onClick={() => window.location.reload()}>
              再読み込み
            </button>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

if (rootElement === null) {
  throw new Error("Root element not found");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </RootErrorBoundary>
  </React.StrictMode>,
);
