module.exports = {
  testEnvironment: "node",
  setupFiles: ["<rootDir>/tests/setup-env.js"],
  collectCoverageFrom: ["src/**/*.js", "!src/index.js"],
  testTimeout: 10000,
  coverageThreshold: {
    global: {
      statements: 90,
      lines: 90,
      functions: 90,
      branches: 85,
    },
  },
};
