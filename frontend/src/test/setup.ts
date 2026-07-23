import "@testing-library/jest-dom/vitest";

const storage: Storage = {
  get length() {
    return Object.keys(storageState).length;
  },
  clear: () => {
    storageState = {};
  },
  getItem: (key: string) => storageState[key] ?? null,
  key: (index: number) => Object.keys(storageState)[index] ?? null,
  removeItem: (key: string) => {
    storageState = Object.fromEntries(
      Object.entries(storageState).filter(([storageKey]) => storageKey !== key),
    );
  },
  setItem: (key: string, value: string) => {
    storageState[key] = value;
  },
};

let storageState: Record<string, string> = {};

Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: storage,
});

Object.defineProperty(window, "localStorage", {
  configurable: true,
  value: storage,
});
