import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    vue({
      // Enable template compilation optimizations
      template: {
        compilerOptions: {
          // Remove whitespace in production
          whitespace: 'condense'
        }
      }
    })
  ],
  server: {
    port: 3000,
    proxy: {
      '/v1': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Core Vue ecosystem
          if (id.includes('vue') || id.includes('@vue')) {
            return 'vue-core'
          }
          
          // Vue Router
          if (id.includes('vue-router')) {
            return 'vue-router'
          }
          
          // Pinia state management
          if (id.includes('pinia')) {
            return 'pinia'
          }
          
          // Telegram WebApp SDK
          if (id.includes('@twa-dev') || id.includes('telegram')) {
            return 'telegram'
          }
          
          // Axios HTTP client
          if (id.includes('axios')) {
            return 'axios'
          }
          
          // UI components and utilities
          if (id.includes('src/components/')) {
            return 'components'
          }
          
          // Views/pages
          if (id.includes('src/views/')) {
            return 'views'
          }
          
          // Composables
          if (id.includes('src/composables/')) {
            return 'composables'
          }
          
          // Stores
          if (id.includes('src/stores/')) {
            return 'stores'
          }
          
          // Node modules (third-party libraries)
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          if (facadeModuleId) {
            const fileName = facadeModuleId.split('/').pop().replace('.vue', '').replace('.js', '')
            return `chunks/[name]-[hash].js`
          }
          return `chunks/[name]-[hash].js`
        },
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/\.(css)$/.test(assetInfo.name)) {
            return `css/[name]-[hash].${ext}`
          }
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
            return `images/[name]-[hash].${ext}`
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
            return `fonts/[name]-[hash].${ext}`
          }
          return `assets/[name]-[hash].${ext}`
        }
      }
    },
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Target modern browsers for better optimization
    target: 'esnext',
    // Enable tree shaking
    treeshake: {
      moduleSideEffects: false
    },
    // Optimize dependencies
    commonjsOptions: {
      include: [/node_modules/]
    },
    // Enable gzip compression
    reportCompressedSize: true,
    // Optimize for production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios']
  },
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false
  }
})
