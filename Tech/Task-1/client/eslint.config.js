/**
 * ESLint configuration — catches common JavaScript/React mistakes during development.
 *
 * Run manually with: npm run lint
 *
 * Rules enabled:
 *   js.configs.recommended          — basic JS best practices
 *   reactHooks.configs.recommended  — enforces Rules of Hooks
 *   reactRefresh.configs.vite       — ensures components are exportable for HMR
 */
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),  // don't lint the production build output
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,  // recognise window, document, etc.
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
  },
])
