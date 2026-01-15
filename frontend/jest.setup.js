// Jest setup file for Next.js Testing Library
import '@testing-library/jest-dom';

// Mock next/router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '',
      query: {},
      asPath: '/',
      push: jest.fn(),
      replace: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
      },
      isReady: true,
      isFallback: false,
      isPreview: false,
    };
  },
}));

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: function MockImage(props) {
    // Return a simple img element for testing
    const { src, alt, width, height, ...rest } = props;
    return {
      type: 'img',
      props: { src, alt, width, height, ...rest },
    };
  },
}));

// Mock next/link
jest.mock('next/link', () => ({
  __esModule: true,
  default: function MockLink({ children, href, ...props }) {
    // Return a simple link element for testing
    return {
      type: 'a',
      props: { href, ...props, children },
    };
  },
}));

// Global test setup
beforeEach(() => {
  // Clear all mocks
  jest.clearAllMocks();

  // Mock localStorage
  const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  global.localStorage = localStorageMock;

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  global.sessionStorage = sessionStorageMock;

  // Mock IntersectionObserver
  global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  };

  // Mock matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
});

// Global test teardown
afterEach(() => {
  // Clean up any DOM elements added during tests
  document.body.innerHTML = '';
});

// Suppress console errors in tests (optional)
global.console = {
  ...console,
  // Uncomment to debug
  // log: console.log,
  // warn: console.warn,
  // error: jest.fn(), // Suppress console errors in tests
};