/**
 * =============================================================================
 * ESLint Configuration — Code Quality & React Best Practices (eslint.config.js)
 * =============================================================================
 *
 * PURPOSE:
 *   Static analysis tool that catches bugs and bad patterns BEFORE runtime.
 *   Uses ESLint v9 "flat config" format (array of config objects).
 *
 * TECH STACK:
 *   - eslint                      — core linter
 *   - @eslint/js                  — recommended JavaScript rules
 *   - eslint-plugin-react-hooks   — enforces React Rules of Hooks
 *   - eslint-plugin-react-refresh — ensures components work with Vite HMR
 *   - globals                     — pre-defined browser globals (window, document)
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Flat config (ESLint 9+) replaces old .eslintrc.json — more explicit, composable
 *   - reactHooks plugin catches: hooks in loops, conditional hooks, missing deps
 *   - reactRefresh plugin: components must be exported for Hot Module Replacement
 *   - globalIgnores(['dist']) — never lint build output (waste of time, false positives)
 *   - Run with: npm run lint (defined in package.json)
 *
 * RULES ENABLED:
 *   js.configs.recommended               — no-unused-vars, no-undef, etc.
 *   reactHooks.configs.flat.recommended  — useEffect deps, hook call order
 *   reactRefresh.configs.vite            — export components for HMR compatibility
 */
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // Exclude production build folder from linting
  globalIgnores(['dist']),

  {
    // Apply these rules to all .js and .jsx source files
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,  // Recognise window, document, fetch, etc. as valid
      parserOptions: { ecmaFeatures: { jsx: true } },  // Allow JSX syntax in .jsx files
    },
  },
])
