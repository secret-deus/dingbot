/**
 * Enhanced Storage Utility
 * Provides robust storage management with error handling, fallback mechanisms, and quota monitoring
 */

// Storage types
const STORAGE_TYPES = {
  LOCAL: 'localStorage',
  SESSION: 'sessionStorage',
  MEMORY: 'memory'
}

// Storage keys
const STORAGE_KEYS = {
  CHAT_HISTORY: 'chatHistory',
  STORAGE_METADATA: 'storageMetadata',
  BACKUP_PREFIX: 'backup_'
}

// Memory storage fallback
const memoryStorage = new Map()

/**
 * Storage Manager Class
 * Handles all storage operations with robust error handling
 */
class StorageManager {
  constructor() {
    this.primaryStorage = null
    this.fallbackStorage = null
    this.currentStorageType = null
    this.isInitialized = false
    this.storageQuota = {
      used: 0,
      available: 0,
      percentage: 0,
      needsCleanup: false
    }
    
    this.initialize()
  }

  /**
   * Initialize storage with fallback detection
   */
  initialize() {
    try {
      // Test localStorage availability
      if (this.isStorageAvailable('localStorage')) {
        this.primaryStorage = window.localStorage
        this.currentStorageType = STORAGE_TYPES.LOCAL
        // localStorage 可用，设为主存储
      } else if (this.isStorageAvailable('sessionStorage')) {
        this.primaryStorage = window.sessionStorage
        this.currentStorageType = STORAGE_TYPES.SESSION
        console.warn('⚠️ localStorage 不可用，使用 sessionStorage')
      } else {
        this.primaryStorage = this.createMemoryStorage()
        this.currentStorageType = STORAGE_TYPES.MEMORY
        console.warn('⚠️ 浏览器存储不可用，使用内存存储')
      }

      // Set fallback storage
      if (this.currentStorageType === STORAGE_TYPES.LOCAL && this.isStorageAvailable('sessionStorage')) {
        this.fallbackStorage = window.sessionStorage
      } else if (this.currentStorageType !== STORAGE_TYPES.MEMORY) {
        this.fallbackStorage = this.createMemoryStorage()
      }

      this.isInitialized = true
      this.updateStorageQuota()
    } catch (error) {
      console.error('存储初始化失败:', error)
      this.primaryStorage = this.createMemoryStorage()
      this.currentStorageType = STORAGE_TYPES.MEMORY
      this.isInitialized = true
    }
  }

  /**
   * Test if a storage type is available
   */
  isStorageAvailable(type) {
    try {
      const storage = window[type]
      const testKey = '__storage_test__'
      storage.setItem(testKey, 'test')
      storage.removeItem(testKey)
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * Create memory storage fallback
   */
  createMemoryStorage() {
    return {
      getItem: (key) => memoryStorage.get(key) || null,
      setItem: (key, value) => memoryStorage.set(key, value),
      removeItem: (key) => memoryStorage.delete(key),
      clear: () => memoryStorage.clear(),
      get length() { return memoryStorage.size },
      key: (index) => Array.from(memoryStorage.keys())[index] || null
    }
  }

  /**
   * Save data with error handling and fallback
   */
  async save(key, data) {
    if (!this.isInitialized) {
      throw new Error('存储管理器未初始化')
    }

    const serializedData = JSON.stringify(data)
    const dataSize = new Blob([serializedData]).size

    try {
      // Check quota before saving
      await this.updateStorageQuota()
      if (this.storageQuota.needsCleanup && dataSize > 1024 * 1024) { // 1MB threshold
        console.warn('存储空间不足，尝试清理')
        await this.cleanup()
      }

      // Create backup before major operations
      if (key === STORAGE_KEYS.CHAT_HISTORY) {
        await this.createBackup(key)
      }

      // Try primary storage
      this.primaryStorage.setItem(key, serializedData)
      // 数据保存成功
      
      // Update metadata
      await this.updateStorageMetadata(key, dataSize)
      
      return true
    } catch (error) {
      console.error(`主存储保存失败 (${this.currentStorageType}):`, error)
      
      // Try fallback storage
      if (this.fallbackStorage) {
        try {
          this.fallbackStorage.setItem(key, serializedData)
          console.log(`✅ 数据已保存到备用存储:`, key)
          return true
        } catch (fallbackError) {
          console.error('备用存储也失败:', fallbackError)
        }
      }
      
      // Handle specific error types
      if (error.name === 'QuotaExceededError' || error.code === 22) {
        throw new StorageQuotaError('存储空间不足，请清理旧数据')
      } else if (error.name === 'SecurityError') {
        throw new StorageSecurityError('存储访问被阻止，请检查浏览器设置')
      } else {
        throw new StorageError(`存储操作失败: ${error.message}`)
      }
    }
  }

  /**
   * Load data with error handling and validation
   */
  async load(key) {
    if (!this.isInitialized) {
      throw new Error('存储管理器未初始化')
    }

    try {
      // Try primary storage first
      const data = this.primaryStorage.getItem(key)
      if (data !== null) {
        const parsed = JSON.parse(data)
        if (this.validateData(key, parsed)) {
          // 数据加载成功
          return parsed
        } else {
          console.warn('主存储数据验证失败，尝试备用存储')
        }
      }
    } catch (error) {
      console.error(`从主存储加载失败 (${this.currentStorageType}):`, error)
    }

    // Try fallback storage
    if (this.fallbackStorage) {
      try {
        const data = this.fallbackStorage.getItem(key)
        if (data !== null) {
          const parsed = JSON.parse(data)
          if (this.validateData(key, parsed)) {
            console.log('✅ 从备用存储加载数据:', key)
            return parsed
          }
        }
      } catch (error) {
        console.error('从备用存储加载失败:', error)
      }
    }

    // Try to restore from backup
    if (key === STORAGE_KEYS.CHAT_HISTORY) {
      const backup = await this.restoreFromBackup(key)
      if (backup) {
        console.log('✅ 从备份恢复数据:', key)
        return backup
      }
    }

    return null
  }

  /**
   * Remove data from storage
   */
  async remove(key) {
    if (!this.isInitialized) {
      throw new Error('存储管理器未初始化')
    }

    try {
      this.primaryStorage.removeItem(key)
      if (this.fallbackStorage) {
        this.fallbackStorage.removeItem(key)
      }
      
      // Update metadata
      await this.updateStorageMetadata(key, 0, true)
      
      console.log('✅ 数据已删除:', key)
      return true
    } catch (error) {
      console.error('删除数据失败:', error)
      throw new StorageError(`删除操作失败: ${error.message}`)
    }
  }

  /**
   * Validate data integrity
   */
  validateData(key, data) {
    try {
      if (!data || typeof data !== 'object') {
        return false
      }

      // Validate chat history data
      if (key === STORAGE_KEYS.CHAT_HISTORY) {
        return (
          data.version &&
          data.sessions &&
          data.sessionHistory &&
          Array.isArray(data.sessionHistory) &&
          data.timestamp
        )
      }

      return true
    } catch (error) {
      console.error('数据验证失败:', error)
      return false
    }
  }

  /**
   * Create backup before major operations
   */
  async createBackup(key) {
    try {
      const data = await this.load(key)
      if (data) {
        const backupKey = `${STORAGE_KEYS.BACKUP_PREFIX}${key}_${Date.now()}`
        this.primaryStorage.setItem(backupKey, JSON.stringify(data))
        
        // Keep only the latest 3 backups
        await this.cleanupOldBackups(key)
        
        console.log('✅ 备份已创建:', backupKey)
      }
    } catch (error) {
      console.warn('创建备份失败:', error)
    }
  }

  /**
   * Restore from backup
   */
  async restoreFromBackup(key) {
    try {
      const backupKeys = []
      const prefix = `${STORAGE_KEYS.BACKUP_PREFIX}${key}_`
      
      // Find all backup keys
      for (let i = 0; i < this.primaryStorage.length; i++) {
        const storageKey = this.primaryStorage.key(i)
        if (storageKey && storageKey.startsWith(prefix)) {
          backupKeys.push(storageKey)
        }
      }
      
      // Sort by timestamp (newest first)
      backupKeys.sort((a, b) => {
        const timestampA = parseInt(a.split('_').pop())
        const timestampB = parseInt(b.split('_').pop())
        return timestampB - timestampA
      })
      
      // Try to restore from the newest backup
      for (const backupKey of backupKeys) {
        try {
          const backupData = this.primaryStorage.getItem(backupKey)
          if (backupData) {
            const parsed = JSON.parse(backupData)
            if (this.validateData(key, parsed)) {
              return parsed
            }
          }
        } catch (error) {
          console.warn(`备份 ${backupKey} 损坏，尝试下一个`)
        }
      }
      
      return null
    } catch (error) {
      console.error('从备份恢复失败:', error)
      return null
    }
  }

  /**
   * Clean up old backups
   */
  async cleanupOldBackups(key, keepCount = 3) {
    try {
      const backupKeys = []
      const prefix = `${STORAGE_KEYS.BACKUP_PREFIX}${key}_`
      
      for (let i = 0; i < this.primaryStorage.length; i++) {
        const storageKey = this.primaryStorage.key(i)
        if (storageKey && storageKey.startsWith(prefix)) {
          backupKeys.push(storageKey)
        }
      }
      
      // Sort by timestamp (newest first)
      backupKeys.sort((a, b) => {
        const timestampA = parseInt(a.split('_').pop())
        const timestampB = parseInt(b.split('_').pop())
        return timestampB - timestampA
      })
      
      // Remove old backups
      const toRemove = backupKeys.slice(keepCount)
      toRemove.forEach(backupKey => {
        this.primaryStorage.removeItem(backupKey)
      })
      
      if (toRemove.length > 0) {
        console.log(`✅ 清理了 ${toRemove.length} 个旧备份`)
      }
    } catch (error) {
      console.warn('清理旧备份失败:', error)
    }
  }

  /**
   * Update storage quota information
   */
  async updateStorageQuota() {
    try {
      if (this.currentStorageType === STORAGE_TYPES.MEMORY) {
        // Memory storage doesn't have quota limits
        this.storageQuota = {
          used: memoryStorage.size * 1024, // Rough estimate
          available: Infinity,
          percentage: 0,
          needsCleanup: false
        }
        return
      }

      // Try to get quota information
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate()
        this.storageQuota = {
          used: estimate.usage || 0,
          available: estimate.quota || 0,
          percentage: estimate.quota ? (estimate.usage / estimate.quota) * 100 : 0,
          needsCleanup: estimate.quota ? (estimate.usage / estimate.quota) > 0.8 : false
        }
      } else {
        // Fallback: estimate based on stored data
        let totalSize = 0
        for (let i = 0; i < this.primaryStorage.length; i++) {
          const key = this.primaryStorage.key(i)
          if (key) {
            const value = this.primaryStorage.getItem(key)
            totalSize += new Blob([value || '']).size
          }
        }
        
        this.storageQuota = {
          used: totalSize,
          available: 5 * 1024 * 1024, // Assume 5MB limit
          percentage: (totalSize / (5 * 1024 * 1024)) * 100,
          needsCleanup: totalSize > 4 * 1024 * 1024 // Cleanup when > 4MB
        }
      }
    } catch (error) {
      console.warn('获取存储配额失败:', error)
      this.storageQuota = {
        used: 0,
        available: 0,
        percentage: 0,
        needsCleanup: false
      }
    }
  }

  /**
   * Update storage metadata
   */
  async updateStorageMetadata(key, size, isRemoval = false) {
    try {
      const metadata = await this.load(STORAGE_KEYS.STORAGE_METADATA) || {
        keys: {},
        totalSize: 0,
        lastUpdated: new Date().toISOString()
      }

      if (isRemoval) {
        if (metadata.keys[key]) {
          metadata.totalSize -= metadata.keys[key].size || 0
          delete metadata.keys[key]
        }
      } else {
        const oldSize = metadata.keys[key]?.size || 0
        metadata.keys[key] = {
          size,
          lastUpdated: new Date().toISOString()
        }
        metadata.totalSize = metadata.totalSize - oldSize + size
      }

      metadata.lastUpdated = new Date().toISOString()
      
      // Save metadata (but don't create backup for metadata itself)
      const serializedData = JSON.stringify(metadata)
      this.primaryStorage.setItem(STORAGE_KEYS.STORAGE_METADATA, serializedData)
    } catch (error) {
      console.warn('更新存储元数据失败:', error)
    }
  }

  /**
   * Cleanup old data to free space
   */
  async cleanup() {
    try {
      console.log('开始清理存储空间...')
      
      // Clean up old backups first
      await this.cleanupOldBackups(STORAGE_KEYS.CHAT_HISTORY, 2)
      
      // Update quota after cleanup
      await this.updateStorageQuota()
      
      console.log('✅ 存储清理完成')
      return true
    } catch (error) {
      console.error('存储清理失败:', error)
      return false
    }
  }

  /**
   * Get storage status information
   */
  getStorageStatus() {
    return {
      type: this.currentStorageType,
      isAvailable: this.isInitialized,
      quota: this.storageQuota,
      hasFallback: !!this.fallbackStorage
    }
  }

  /**
   * Format bytes to human readable string
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * Reset storage to clean state
   */
  async resetToCleanState() {
    try {
      console.warn('重置存储到干净状态...')
      
      // Clear all chat-related data
      const keysToRemove = []
      for (let i = 0; i < this.primaryStorage.length; i++) {
        const key = this.primaryStorage.key(i)
        if (key && (
          key === STORAGE_KEYS.CHAT_HISTORY ||
          key.startsWith(STORAGE_KEYS.BACKUP_PREFIX) ||
          key === STORAGE_KEYS.STORAGE_METADATA
        )) {
          keysToRemove.push(key)
        }
      }
      
      keysToRemove.forEach(key => {
        this.primaryStorage.removeItem(key)
      })
      
      // Clear fallback storage too
      if (this.fallbackStorage) {
        keysToRemove.forEach(key => {
          this.fallbackStorage.removeItem(key)
        })
      }
      
      // Clear memory storage
      memoryStorage.clear()
      
      console.log('✅ 存储已重置到干净状态')
      return true
    } catch (error) {
      console.error('重置存储失败:', error)
      return false
    }
  }
}

// Custom error classes
class StorageError extends Error {
  constructor(message) {
    super(message)
    this.name = 'StorageError'
  }
}

class StorageQuotaError extends StorageError {
  constructor(message) {
    super(message)
    this.name = 'StorageQuotaError'
  }
}

class StorageSecurityError extends StorageError {
  constructor(message) {
    super(message)
    this.name = 'StorageSecurityError'
  }
}

// Create singleton instance
const storageManager = new StorageManager()

export {
  storageManager,
  StorageError,
  StorageQuotaError,
  StorageSecurityError,
  STORAGE_TYPES,
  STORAGE_KEYS
}