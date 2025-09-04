/**
 * DOM utility functions
 */
export class DOMUtils {
    /**
     * Escape HTML to prevent XSS
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Generate unique ID
     */
    static generateId(prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Get element by ID with error handling
     */
    static getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    }
    
    /**
     * Add class with error handling
     */
    static addClass(element, className) {
        if (element && element.classList) {
            element.classList.add(className);
        }
    }
    
    /**
     * Remove class with error handling
     */
    static removeClass(element, className) {
        if (element && element.classList) {
            element.classList.remove(className);
        }
    }
    
    /**
     * Toggle class with error handling
     */
    static toggleClass(element, className) {
        if (element && element.classList) {
            return element.classList.toggle(className);
        }
        return false;
    }
    
    /**
     * Scroll element to bottom
     */
    static scrollToBottom(element) {
        if (element) {
            element.scrollTop = element.scrollHeight;
        }
    }
    
    /**
     * Format date for display
     */
    static formatDate(date) {
        return new Date(date).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}
