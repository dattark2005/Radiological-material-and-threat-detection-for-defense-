/**
 * Advanced Real-Time Notification System
 * Provides premium notification experience with real-time updates
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 50;
        this.notificationId = 0;
        this.soundEnabled = true;
        this.notificationsEnabled = true;
        this.subtleMode = true; // New: subtle mode by default
        this.isInitialized = false;
        
        this.init();
    }

    init() {
        console.log('🔔 Initializing Advanced Notification System...');
        this.createNotificationContainer();
        this.setupNotificationCenter();
        this.startRealTimeUpdates();
        this.setupSoundSystem();
        this.isInitialized = true;
        console.log('✅ Notification System initialized');
    }

    createNotificationContainer() {
        // Create floating notification container
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);

        // Create notification center panel
        const centerPanel = document.createElement('div');
        centerPanel.id = 'notificationCenterPanel';
        centerPanel.className = 'notification-center-panel';
        centerPanel.innerHTML = `
            <div class="notification-center-header">
                <div class="header-content">
                    <h3><i class="fas fa-bell"></i> Notification Center</h3>
                    <div class="header-actions">
                        <button class="btn-icon" id="markAllReadBtn" title="Mark all as read">
                            <i class="fas fa-check-double"></i>
                        </button>
                        <button class="btn-icon" id="clearAllBtn" title="Clear all">
                            <i class="fas fa-trash"></i>
                        </button>
                        <button class="btn-icon" id="closeNotificationCenter" title="Close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="notification-center-body">
                <div class="notification-filters">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="system">System</button>
                    <button class="filter-btn" data-filter="analysis">Analysis</button>
                    <button class="filter-btn" data-filter="security">Security</button>
                    <button class="filter-btn" data-filter="error">Errors</button>
                </div>
                <div class="notification-list" id="notificationList">
                    <div class="no-notifications">
                        <i class="fas fa-bell-slash"></i>
                        <p>No notifications yet</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(centerPanel);
    }

    setupNotificationCenter() {
        const notificationBtn = document.getElementById('notificationBtn');
        const centerPanel = document.getElementById('notificationCenterPanel');
        const closeBtn = document.getElementById('closeNotificationCenter');
        const markAllReadBtn = document.getElementById('markAllReadBtn');
        const clearAllBtn = document.getElementById('clearAllBtn');

        // Toggle notification center
        if (notificationBtn) {
            notificationBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNotificationCenter();
            });
        }

        // Close notification center
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeNotificationCenter();
            });
        }

        // Mark all as read
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }

        // Clear all notifications
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllNotifications();
            });
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.filterNotifications(e.target.dataset.filter);
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!centerPanel.contains(e.target) && !notificationBtn?.contains(e.target)) {
                this.closeNotificationCenter();
            }
        });
    }

    // Real-time notification creation (Non-intrusive mode)
    createNotification(type, title, message, options = {}) {
        const notification = {
            id: ++this.notificationId,
            type: type,
            title: title,
            message: message,
            timestamp: new Date(),
            read: false,
            persistent: options.persistent || false,
            action: options.action || null,
            icon: options.icon || this.getTypeIcon(type),
            priority: options.priority || 'normal',
            category: options.category || 'system'
        };

        this.notifications.unshift(notification);
        
        // Limit notifications
        if (this.notifications.length > this.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.maxNotifications);
        }

        // Respect user preferences for notification display
        if (!this.notificationsEnabled) {
            // If notifications are disabled, only update the center
            return notification.id;
        }
        
        // In subtle mode, only show floating notifications for critical events
        if (this.subtleMode) {
            if (type === 'error' || options.priority === 'high' || options.forceShow) {
                this.showFloatingNotification(notification);
            } else {
                // For normal notifications, just show subtle badge animation
                this.showSubtleNotification(notification);
            }
        } else {
            // Normal mode - show all floating notifications
            this.showFloatingNotification(notification);
        }
        
        // Update notification center
        this.updateNotificationCenter();
        
        // Update badge count with animation
        this.updateNotificationBadge();
        
        // Play subtle sound only for important notifications
        if (this.soundEnabled && (type === 'error' || options.priority === 'high')) {
            this.playNotificationSound(type);
        }

        return notification.id;
    }

    showFloatingNotification(notification) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notificationEl = document.createElement('div');
        notificationEl.className = `notification-toast notification-${notification.type} notification-priority-${notification.priority}`;
        notificationEl.dataset.id = notification.id;
        
        notificationEl.innerHTML = `
            <div class="notification-icon">
                <i class="${notification.icon}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${this.formatTime(notification.timestamp)}</div>
            </div>
            <div class="notification-actions">
                ${notification.action ? `<button class="notification-action-btn" onclick="${notification.action}">Action</button>` : ''}
                <button class="notification-close" onclick="notificationSystem.removeFloatingNotification(${notification.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-progress"></div>
        `;

        // Add entrance animation
        notificationEl.style.transform = 'translateX(100%)';
        notificationEl.style.opacity = '0';
        
        container.appendChild(notificationEl);
        
        // Trigger animation
        requestAnimationFrame(() => {
            notificationEl.style.transform = 'translateX(0)';
            notificationEl.style.opacity = '1';
        });

        // Add click to mark as read
        notificationEl.addEventListener('click', () => {
            this.markAsRead(notification.id);
        });
    }

    showSubtleNotification(notification) {
        // Instead of floating notification, just animate the notification bell
        const notificationBtn = document.getElementById('notificationBtn');
        const badge = document.getElementById('notificationBadge');
        
        if (notificationBtn) {
            // Add subtle pulse animation to the bell
            notificationBtn.classList.add('subtle-notification');
            setTimeout(() => {
                notificationBtn.classList.remove('subtle-notification');
            }, 2000);
        }
        
        if (badge) {
            // Add brief glow to the badge
            badge.classList.add('new-notification');
            setTimeout(() => {
                badge.classList.remove('new-notification');
            }, 3000);
        }
        
        // Show brief status in browser title (non-intrusive)
        if (notification.type === 'success' || notification.type === 'analysis') {
            const originalTitle = document.title;
            document.title = `✓ ${notification.title} - ${originalTitle}`;
            setTimeout(() => {
                document.title = originalTitle;
            }, 3000);
        }
    }

    removeFloatingNotification(id) {
        const notificationEl = document.querySelector(`[data-id="${id}"]`);
        if (notificationEl) {
            notificationEl.style.transform = 'translateX(100%)';
            notificationEl.style.opacity = '0';
            setTimeout(() => {
                if (notificationEl.parentNode) {
                    notificationEl.parentNode.removeChild(notificationEl);
                }
            }, 300);
        }
    }

    updateNotificationCenter() {
        const notificationList = document.getElementById('notificationList');
        if (!notificationList) return;

        if (this.notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="no-notifications">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications yet</p>
                </div>
            `;
            return;
        }

        notificationList.innerHTML = this.notifications.map(notification => `
            <div class="notification-item ${notification.read ? 'read' : 'unread'}" data-id="${notification.id}" data-category="${notification.category}">
                <div class="notification-item-icon">
                    <i class="${notification.icon}"></i>
                </div>
                <div class="notification-item-content">
                    <div class="notification-item-header">
                        <span class="notification-item-title">${notification.title}</span>
                        <span class="notification-item-time">${this.formatTimeAgo(notification.timestamp)}</span>
                    </div>
                    <div class="notification-item-message">${notification.message}</div>
                    <div class="notification-item-category">${notification.category.toUpperCase()}</div>
                </div>
                <div class="notification-item-actions">
                    ${!notification.read ? '<div class="unread-indicator"></div>' : ''}
                    <button class="btn-icon-small" onclick="notificationSystem.removeNotification(${notification.id})" title="Remove">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');

        // Add click handlers
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                this.markAsRead(id);
            });
        });
    }

    updateNotificationBadge() {
        const badge = document.getElementById('notificationBadge');
        if (!badge) return;

        const unreadCount = this.notifications.filter(n => !n.read).length;
        
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'flex';
            badge.classList.add('pulse');
        } else {
            badge.style.display = 'none';
            badge.classList.remove('pulse');
        }
    }

    // Real-time updates (Less intrusive)
    startRealTimeUpdates() {
        // Simulate real-time system notifications (less frequent)
        setInterval(() => {
            this.generateSystemNotifications();
        }, 120000); // Every 2 minutes (reduced from 30 seconds)

        // Update time displays
        setInterval(() => {
            this.updateTimeDisplays();
        }, 60000); // Every minute

        // Check for analysis completion (only when analysis is running)
        setInterval(() => {
            if (window.currentAnalysisSession) {
                this.checkAnalysisStatus();
            }
        }, 10000); // Every 10 seconds (reduced frequency)

        // System health monitoring (less frequent, only for critical issues)
        setInterval(() => {
            this.monitorSystemHealth();
        }, 60000); // Every minute (reduced from 15 seconds)
    }

    generateSystemNotifications() {
        const systemEvents = [
            { type: 'info', title: 'System Status', message: 'All systems operating normally', category: 'system' },
            { type: 'success', title: 'Backup Complete', message: 'Daily backup completed successfully', category: 'system' },
            { type: 'warning', title: 'High CPU Usage', message: 'CPU usage is above 80%', category: 'system' },
            { type: 'info', title: 'New User Login', message: 'User logged in from new location', category: 'security' }
        ];

        // Reduced chance and only for important events
        if (Math.random() < 0.1) { // 10% chance (reduced from 30%)
            const event = systemEvents[Math.floor(Math.random() * systemEvents.length)];
            // Only create notification if it's important (warning or success)
            if (event.type === 'warning' || event.type === 'success') {
                this.createNotification(event.type, event.title, event.message, { category: event.category });
            }
        }
    }

    checkAnalysisStatus() {
        // Only update the notification center, don't create new notifications for progress
        // Analysis start/completion notifications are handled by the main analysis functions
        if (window.currentAnalysisSession) {
            // Just update the notification center silently
            this.updateNotificationCenter();
        }
    }

    monitorSystemHealth() {
        // Simulate system health monitoring
        const metrics = {
            cpu: Math.random() * 100,
            memory: Math.random() * 100,
            disk: Math.random() * 100
        };

        if (metrics.cpu > 90) {
            this.createNotification('error', 'System Alert', 'Critical CPU usage detected!', { 
                category: 'system',
                priority: 'high'
            });
        }

        if (metrics.memory > 85) {
            this.createNotification('warning', 'Memory Warning', 'High memory usage detected', { 
                category: 'system' 
            });
        }
    }

    // Notification center methods
    toggleNotificationCenter() {
        const panel = document.getElementById('notificationCenterPanel');
        if (panel) {
            panel.classList.toggle('show');
            if (panel.classList.contains('show')) {
                this.updateNotificationCenter();
            }
        }
    }

    closeNotificationCenter() {
        const panel = document.getElementById('notificationCenterPanel');
        if (panel) {
            panel.classList.remove('show');
        }
    }

    markAsRead(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
            notification.read = true;
            this.updateNotificationCenter();
            this.updateNotificationBadge();
        }
    }

    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.updateNotificationCenter();
        this.updateNotificationBadge();
        this.createNotification('success', 'Notifications', 'All notifications marked as read', { category: 'system' });
    }

    clearAllNotifications() {
        this.notifications = [];
        this.updateNotificationCenter();
        this.updateNotificationBadge();
        
        // Clear floating notifications
        const container = document.getElementById('notificationContainer');
        if (container) {
            container.innerHTML = '';
        }
    }

    removeNotification(id) {
        this.notifications = this.notifications.filter(n => n.id !== id);
        this.updateNotificationCenter();
        this.updateNotificationBadge();
        this.removeFloatingNotification(id);
    }

    filterNotifications(filter) {
        const items = document.querySelectorAll('.notification-item');
        items.forEach(item => {
            if (filter === 'all' || item.dataset.category === filter) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // Sound system
    setupSoundSystem() {
        this.sounds = {
            success: this.createSound(800, 0.1, 'sine'),
            error: this.createSound(300, 0.2, 'square'),
            warning: this.createSound(600, 0.15, 'triangle'),
            info: this.createSound(500, 0.05, 'sine')
        };
    }

    createSound(frequency, duration, type = 'sine') {
        return () => {
            if (!this.soundEnabled) return;
            
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = frequency;
                oscillator.type = type;
                
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + duration);
            } catch (e) {
                console.warn('Audio not supported:', e);
            }
        };
    }

    playNotificationSound(type) {
        if (this.sounds[type]) {
            this.sounds[type]();
        }
    }

    // Utility methods
    getTypeIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle',
            system: 'fas fa-cog',
            analysis: 'fas fa-chart-line',
            security: 'fas fa-shield-alt'
        };
        return icons[type] || icons.info;
    }

    getAutoRemoveDelay(type) {
        const delays = {
            success: 4000,
            info: 3000,
            warning: 6000,
            error: 8000
        };
        return delays[type] || 4000;
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ago`;
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return 'Just now';
    }

    updateTimeDisplays() {
        document.querySelectorAll('.notification-item-time').forEach((el, index) => {
            if (this.notifications[index]) {
                el.textContent = this.formatTimeAgo(this.notifications[index].timestamp);
            }
        });
    }

    // Public API methods
    success(title, message, options = {}) {
        return this.createNotification('success', title, message, options);
    }

    error(title, message, options = {}) {
        return this.createNotification('error', title, message, options);
    }

    warning(title, message, options = {}) {
        return this.createNotification('warning', title, message, options);
    }

    info(title, message, options = {}) {
        return this.createNotification('info', title, message, options);
    }

    system(title, message, options = {}) {
        return this.createNotification('system', title, message, { ...options, category: 'system' });
    }

    analysis(title, message, options = {}) {
        return this.createNotification('analysis', title, message, { ...options, category: 'analysis' });
    }

    security(title, message, options = {}) {
        return this.createNotification('security', title, message, { ...options, category: 'security' });
    }

    // Settings methods
    toggleSubtleMode() {
        this.subtleMode = !this.subtleMode;
        const mode = this.subtleMode ? 'Subtle' : 'Normal';
        this.createNotification('info', 'Notification Mode', `Switched to ${mode} mode`, { 
            forceShow: true,
            category: 'system' 
        });
        console.log(`🔔 Notification mode: ${mode}`);
        return this.subtleMode;
    }

    toggleNotifications() {
        this.notificationsEnabled = !this.notificationsEnabled;
        const status = this.notificationsEnabled ? 'enabled' : 'disabled';
        console.log(`🔔 Notifications ${status}`);
        return this.notificationsEnabled;
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        const status = this.soundEnabled ? 'enabled' : 'disabled';
        console.log(`🔊 Notification sounds ${status}`);
        return this.soundEnabled;
    }
}

// Initialize notification system
let notificationSystem;

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        notificationSystem = new NotificationSystem();
        
        // Replace old showNotification function
        window.showNotification = function(message, type = 'info', title = null) {
            const notificationTitle = title || type.charAt(0).toUpperCase() + type.slice(1);
            notificationSystem.createNotification(type, notificationTitle, message);
        };
        
        // Welcome notification
        setTimeout(() => {
            notificationSystem.success('System Ready', 'Radiological Threat Detection System is online and ready for operation');
        }, 1000);
        
        console.log('✅ Advanced Notification System ready');
    }, 2000);
});

// Export for global access
window.NotificationSystem = NotificationSystem;
