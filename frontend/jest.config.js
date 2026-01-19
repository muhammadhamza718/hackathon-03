const nextJest = require('next/jest');

/** @type {import('jest').Config} */
const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
});

// Add any custom config to be passed to Jest
/** @type {import('jest').Config} */
const customJestConfig = {
  // Add more setup options before each test is run
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Test environment
  testEnvironment: 'jest-environment-jsdom',

  // Module name mappings for imports
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },

  // Coverage configuration
  coverageDirectory: 'coverage',
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/coverage/',
    '/tests/',
    '/scripts/',
  ],
  // Coverage thresholds to enforce >90% coverage
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    // Component-level thresholds for critical paths
    './src/store/auth-context.tsx': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
    './src/store/editor-store.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/lib/api-client.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/lib/mcp/client.ts': {
      branches: 85, // More complex, slightly lower threshold
      functions: 85,
      lines: 85,
      statements: 85,
    },
  },

  // Test match patterns
  testMatch: [
    '**/tests/unit/**/*.test.{js,jsx,ts,tsx}',
    '**/tests/infrastructure/**/*.test.{js,jsx,ts,tsx}',
    '**/__tests__/*.{js,jsx,ts,tsx}',
  ],

  // Transform patterns
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },

  // Ignore patterns - Jest doesn't support ignorePatterns, using testPathIgnorePatterns instead
  testPathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/coverage/',
    '/tests/integration/',
    '/tests/e2e/',
    '/tests/performance/',
    '/tests/security/',
  ],

  // Verbose output
  verbose: true,

  // Collect coverage from source files
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/**/index.{js,jsx,ts,tsx}',
  ],

  // Maximum number of concurrent workers
  maxWorkers: '50%',

  // Pass test results with test names
  passWithNoTests: true,

  // Clear mock calls between tests
  clearMocks: true,

  // Reset modules between tests
  resetModules: true,
};

module.exports = customJestConfig;