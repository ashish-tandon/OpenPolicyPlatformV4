import { test, expect } from '@playwright/test'

test.describe('Performance Tests', () => {
  test('should load home page within 3 seconds', async ({ page }) => {
    const startTime = Date.now()
    
    await page.goto('/', { waitUntil: 'networkidle' })
    
    const loadTime = Date.now() - startTime
    expect(loadTime).toBeLessThan(3000)
    
    // Check Core Web Vitals
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        let lcp, fid, cls
        
        // Largest Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries()
          lcp = entries[entries.length - 1].startTime
        }).observe({ entryTypes: ['largest-contentful-paint'] })
        
        // First Input Delay
        new PerformanceObserver((list) => {
          const entries = list.getEntries()
          fid = entries[0].processingStart - entries[0].startTime
        }).observe({ entryTypes: ['first-input'] })
        
        // Cumulative Layout Shift
        let clsValue = 0
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value
            }
          }
          cls = clsValue
        }).observe({ entryTypes: ['layout-shift'] })
        
        // Wait and collect metrics
        setTimeout(() => {
          resolve({ lcp, fid, cls })
        }, 2000)
      })
    })
    
    console.log('Core Web Vitals:', metrics)
    
    // Assert on metrics (adjust thresholds as needed)
    if (metrics.lcp) expect(metrics.lcp).toBeLessThan(2500) // Good LCP
    if (metrics.cls) expect(metrics.cls).toBeLessThan(0.1) // Good CLS
  })

  test('should handle concurrent requests efficiently', async ({ page }) => {
    await page.goto('/policies')
    
    // Measure concurrent API calls
    const apiCalls = await page.evaluate(async () => {
      const promises = []
      const timings = []
      
      // Simulate 10 concurrent API calls
      for (let i = 0; i < 10; i++) {
        const start = performance.now()
        promises.push(
          fetch('/api/policies?page=' + i)
            .then(() => {
              timings.push(performance.now() - start)
            })
        )
      }
      
      await Promise.all(promises)
      return {
        average: timings.reduce((a, b) => a + b) / timings.length,
        max: Math.max(...timings),
        min: Math.min(...timings)
      }
    })
    
    console.log('API Call Timings:', apiCalls)
    
    // All requests should complete within reasonable time
    expect(apiCalls.average).toBeLessThan(500)
    expect(apiCalls.max).toBeLessThan(1000)
  })

  test('should efficiently render large lists', async ({ page }) => {
    await page.goto('/representatives')
    
    // Measure render performance
    const renderMetrics = await page.evaluate(() => {
      const observer = new PerformanceObserver(() => {})
      observer.observe({ entryTypes: ['measure'] })
      
      performance.mark('render-start')
      
      // Wait for all representative cards to render
      return new Promise((resolve) => {
        const checkCards = () => {
          const cards = document.querySelectorAll('[data-cy=representative-card]')
          if (cards.length > 50) {
            performance.mark('render-end')
            performance.measure('render-time', 'render-start', 'render-end')
            
            const measure = performance.getEntriesByName('render-time')[0]
            resolve({
              renderTime: measure.duration,
              cardCount: cards.length
            })
          } else {
            requestAnimationFrame(checkCards)
          }
        }
        checkCards()
      })
    })
    
    console.log('Render Metrics:', renderMetrics)
    
    // Should render efficiently even with many items
    expect(renderMetrics.renderTime).toBeLessThan(1000)
  })

  test('should have minimal memory leaks', async ({ page }) => {
    await page.goto('/')
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize
      }
      return 0
    })
    
    // Navigate through multiple pages
    const pages = ['/policies', '/representatives', '/committees', '/dashboard']
    for (const path of pages) {
      await page.goto(path)
      await page.waitForLoadState('networkidle')
    }
    
    // Force garbage collection if available
    await page.evaluate(() => {
      if (window.gc) {
        window.gc()
      }
    })
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize
      }
      return 0
    })
    
    // Memory increase should be reasonable
    const memoryIncrease = finalMemory - initialMemory
    const increasePercentage = (memoryIncrease / initialMemory) * 100
    
    console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${increasePercentage.toFixed(2)}%)`)
    
    // Expect less than 50% memory increase
    expect(increasePercentage).toBeLessThan(50)
  })

  test('should optimize image loading', async ({ page }) => {
    await page.goto('/representatives')
    
    // Check image optimization
    const imageStats = await page.evaluate(() => {
      const images = Array.from(document.querySelectorAll('img'))
      let lazyLoaded = 0
      let optimizedFormats = 0
      let appropriateSizes = 0
      
      images.forEach(img => {
        // Check lazy loading
        if (img.loading === 'lazy') lazyLoaded++
        
        // Check for modern formats
        if (img.src.includes('.webp') || img.src.includes('.avif')) {
          optimizedFormats++
        }
        
        // Check if image size is appropriate
        if (img.naturalWidth > 0 && img.width > 0) {
          const ratio = img.naturalWidth / img.width
          if (ratio < 2.5) appropriateSizes++
        }
      })
      
      return {
        total: images.length,
        lazyLoaded,
        optimizedFormats,
        appropriateSizes
      }
    })
    
    console.log('Image Optimization Stats:', imageStats)
    
    // Most images should be optimized
    expect(imageStats.lazyLoaded / imageStats.total).toBeGreaterThan(0.8)
  })

  test('should handle slow network gracefully', async ({ page, context }) => {
    // Simulate slow 3G
    await context.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.continue()
    })
    
    await page.goto('/')
    
    // Should show loading states
    await expect(page.locator('[data-cy=loading-skeleton]')).toBeVisible()
    
    // Content should eventually load
    await expect(page.locator('[data-cy=hero-section]')).toBeVisible({ timeout: 10000 })
  })

  test('should cache resources effectively', async ({ page }) => {
    // First visit
    await page.goto('/')
    
    // Get resource timings
    const firstLoadResources = await page.evaluate(() => {
      return performance.getEntriesByType('resource').map(r => ({
        name: r.name,
        duration: r.duration,
        transferSize: r.transferSize
      }))
    })
    
    // Second visit (should use cache)
    await page.reload()
    
    const secondLoadResources = await page.evaluate(() => {
      return performance.getEntriesByType('resource').map(r => ({
        name: r.name,
        duration: r.duration,
        transferSize: r.transferSize
      }))
    })
    
    // Compare cache effectiveness
    let cachedResources = 0
    secondLoadResources.forEach(resource => {
      const firstLoad = firstLoadResources.find(r => r.name === resource.name)
      if (firstLoad && resource.transferSize === 0) {
        cachedResources++
      }
    })
    
    const cacheRatio = cachedResources / secondLoadResources.length
    console.log(`Cache ratio: ${(cacheRatio * 100).toFixed(2)}%`)
    
    // Expect good cache usage
    expect(cacheRatio).toBeGreaterThan(0.5)
  })
})