import { DOMUtils } from '../utils/dom.js';
import { CONSTANTS } from '../utils/constants.js';

/**
 * Notification manager for user feedback
 */
export class NotificationManager {
    constructor(container) {
        this.container = container;
    }
    
    /**
     * Show notification message
     */
    show(message, type = CONSTANTS.NOTIFICATION_TYPES.INFO) {
        const notification = document.createElement('div');
        notification.className = `message assistant-message ${type}`;
        notification.innerHTML = message;
        
        this.container.appendChild(notification);
        DOMUtils.scrollToBottom(this.container);
        
        return notification;
    }
    
    /**
     * Show success notification
     */
    success(message) {
        return this.show(message, CONSTANTS.NOTIFICATION_TYPES.SUCCESS);
    }
    
    /**
     * Show error notification
     */
    error(message) {
        return this.show(message, CONSTANTS.NOTIFICATION_TYPES.ERROR);
    }
    
    /**
     * Show info notification
     */
    info(message) {
        return this.show(message, CONSTANTS.NOTIFICATION_TYPES.INFO);
    }
    
    /**
     * Show loading notification with animation
     */
    showLoading(baseText = '📖 Je cherche') {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message loading';
        loadingDiv.id = 'loading-message';
        
        let dots = '';
        loadingDiv.textContent = baseText + '...';
        
        // Animation interval
        const animation = setInterval(() => {
            dots = dots.length >= 3 ? '' : dots + '.';
            if (document.getElementById('loading-message')) {
                loadingDiv.textContent = baseText + dots + ' 📖';
            } else {
                clearInterval(animation);
            }
        }, CONSTANTS.UI.LOADING_ANIMATION_INTERVAL);
        
        this.container.appendChild(loadingDiv);
        DOMUtils.scrollToBottom(this.container);
        
        return {
            element: loadingDiv,
            stop: () => {
                clearInterval(animation);
                if (loadingDiv.parentNode) {
                    loadingDiv.remove();
                }
            }
        };
    }
    
    /**
     * Remove loading notification
     */
    removeLoading() {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.remove();
        }
    }
}
