#!/usr/bin/env node

/**
 * Bundle analysis script for Vite build optimization.
 * 
 * Analyzes the build output and provides recommendations for optimization.
 */

import { readFileSync, readdirSync, statSync } from 'fs'
import { join, extname } from 'path'

const DIST_DIR = 'dist'
const CHUNKS_DIR = join(DIST_DIR, 'chunks')
const JS_DIR = join(DIST_DIR, 'js')
const CSS_DIR = join(DIST_DIR, 'css')

/**
 * Get file size in bytes
 */
function getFileSize(filePath) {
  try {
    const stats = statSync(filePath)
    return stats.size
  } catch (error) {
    return 0
  }
}

/**
 * Format bytes to human readable format
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * Analyze JavaScript chunks
 */
function analyzeJSChunks() {
  const chunks = []
  
  try {
    const files = readdirSync(JS_DIR)
    files.forEach(file => {
      if (extname(file) === '.js') {
        const filePath = join(JS_DIR, file)
        const size = getFileSize(filePath)
        chunks.push({
          name: file,
          size,
          formattedSize: formatBytes(size),
          type: 'js'
        })
      }
    })
  } catch (error) {
    console.warn('JS directory not found:', error.message)
  }
  
  try {
    const files = readdirSync(CHUNKS_DIR)
    files.forEach(file => {
      if (extname(file) === '.js') {
        const filePath = join(CHUNKS_DIR, file)
        const size = getFileSize(filePath)
        chunks.push({
          name: file,
          size,
          formattedSize: formatBytes(size),
          type: 'chunk'
        })
      }
    })
  } catch (error) {
    console.warn('Chunks directory not found:', error.message)
  }
  
  return chunks.sort((a, b) => b.size - a.size)
}

/**
 * Analyze CSS files
 */
function analyzeCSSFiles() {
  const cssFiles = []
  
  try {
    const files = readdirSync(CSS_DIR)
    files.forEach(file => {
      if (extname(file) === '.css') {
        const filePath = join(CSS_DIR, file)
        const size = getFileSize(filePath)
        cssFiles.push({
          name: file,
          size,
          formattedSize: formatBytes(size),
          type: 'css'
        })
      }
    })
  } catch (error) {
    console.warn('CSS directory not found:', error.message)
  }
  
  return cssFiles.sort((a, b) => b.size - a.size)
}

/**
 * Get optimization recommendations
 */
function getRecommendations(jsChunks, cssFiles) {
  const recommendations = []
  
  // Check for large chunks
  const largeChunks = jsChunks.filter(chunk => chunk.size > 200000) // > 200KB
  if (largeChunks.length > 0) {
    recommendations.push({
      type: 'warning',
      message: `Large chunks detected: ${largeChunks.map(c => `${c.name} (${c.formattedSize})`).join(', ')}`,
      suggestion: 'Consider splitting large chunks further or lazy loading components'
    })
  }
  
  // Check for too many chunks
  if (jsChunks.length > 20) {
    recommendations.push({
      type: 'info',
      message: `Many chunks detected (${jsChunks.length})`,
      suggestion: 'Consider consolidating small chunks to reduce HTTP requests'
    })
  }
  
  // Check for large CSS files
  const largeCSS = cssFiles.filter(file => file.size > 100000) // > 100KB
  if (largeCSS.length > 0) {
    recommendations.push({
      type: 'warning',
      message: `Large CSS files detected: ${largeCSS.map(f => `${f.name} (${f.formattedSize})`).join(', ')}`,
      suggestion: 'Consider CSS optimization or splitting stylesheets'
    })
  }
  
  // Check for vendor chunk size
  const vendorChunk = jsChunks.find(chunk => chunk.name.includes('vendor'))
  if (vendorChunk && vendorChunk.size > 500000) { // > 500KB
    recommendations.push({
      type: 'warning',
      message: `Large vendor chunk detected: ${vendorChunk.formattedSize}`,
      suggestion: 'Consider splitting vendor libraries or using tree shaking'
    })
  }
  
  return recommendations
}

/**
 * Main analysis function
 */
function analyzeBundle() {
  console.log('🔍 Analyzing bundle size...\n')
  
  const jsChunks = analyzeJSChunks()
  const cssFiles = analyzeCSSFiles()
  
  const totalJSSize = jsChunks.reduce((sum, chunk) => sum + chunk.size, 0)
  const totalCSSSize = cssFiles.reduce((sum, file) => sum + file.size, 0)
  const totalSize = totalJSSize + totalCSSSize
  
  console.log('📊 Bundle Analysis Results')
  console.log('=' .repeat(50))
  
  console.log('\n📦 JavaScript Chunks:')
  console.log('-'.repeat(30))
  jsChunks.forEach(chunk => {
    const percentage = ((chunk.size / totalJSSize) * 100).toFixed(1)
    console.log(`${chunk.name.padEnd(25)} ${chunk.formattedSize.padStart(10)} (${percentage}%)`)
  })
  
  console.log('\n🎨 CSS Files:')
  console.log('-'.repeat(30))
  cssFiles.forEach(file => {
    const percentage = ((file.size / totalCSSSize) * 100).toFixed(1)
    console.log(`${file.name.padEnd(25)} ${file.formattedSize.padStart(10)} (${percentage}%)`)
  })
  
  console.log('\n📈 Summary:')
  console.log('-'.repeat(30))
  console.log(`Total JS Size:     ${formatBytes(totalJSSize).padStart(10)}`)
  console.log(`Total CSS Size:    ${formatBytes(totalCSSSize).padStart(10)}`)
  console.log(`Total Bundle Size: ${formatBytes(totalSize).padStart(10)}`)
  console.log(`Chunk Count:       ${jsChunks.length.toString().padStart(10)}`)
  
  // Performance thresholds
  const performanceThresholds = {
    excellent: 500000,  // < 500KB
    good: 1000000,     // < 1MB
    acceptable: 2000000, // < 2MB
    poor: 5000000      // > 5MB
  }
  
  let performanceRating = 'poor'
  if (totalSize < performanceThresholds.excellent) {
    performanceRating = 'excellent'
  } else if (totalSize < performanceThresholds.good) {
    performanceRating = 'good'
  } else if (totalSize < performanceThresholds.acceptable) {
    performanceRating = 'acceptable'
  }
  
  console.log(`\n⚡ Performance Rating: ${performanceRating.toUpperCase()}`)
  
  // Get recommendations
  const recommendations = getRecommendations(jsChunks, cssFiles)
  
  if (recommendations.length > 0) {
    console.log('\n💡 Recommendations:')
    console.log('-'.repeat(30))
    recommendations.forEach(rec => {
      const icon = rec.type === 'warning' ? '⚠️' : 'ℹ️'
      console.log(`${icon} ${rec.message}`)
      console.log(`   → ${rec.suggestion}`)
    })
  }
  
  console.log('\n✅ Bundle analysis complete!')
}

// Run analysis
analyzeBundle()
